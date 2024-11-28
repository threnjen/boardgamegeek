import argparse
import os
import sys
import time
import boto3
import xml.etree.ElementTree as ET
from datetime import datetime
from functools import partial

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy_settings import *
from modules.bgg_scraper.spiders import GameSpider, UserSpider

from config import CONFIGS
from utils.file_handler import FileHandler
from utils.s3_file_handler import S3FileHandler
from utils.local_file_handler import LocalFileHandler
from utils.processing_functions import (
    get_local_keys_based_on_env,
    load_file_local_first,
    save_file_local_first,
)

S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")
IS_LOCAL = True if os.environ.get("IS_LOCAL", "False").lower() == "true" else False
ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
WORKING_DIR = (
    CONFIGS["dev_directory"] if ENVIRONMENT == "dev" else CONFIGS["prod_directory"]
)


class DataScraper:

    def __init__(self, scraper_type: str, urls_filename: str) -> None:
        self.file_group = urls_filename.split("_")[0]
        self.urls_filename = urls_filename.split(".")[0]
        self.bot_scraper_name = CONFIGS[scraper_type]["scrapy_bot_name"]
        self.raw_urls_folder = CONFIGS[scraper_type]["raw_urls_directory"]
        self.scraped_files_folder = CONFIGS[scraper_type]["output_xml_directory"]
        self.scraper_type = scraper_type

    def scraper_process_chain(self):
        scraper_urls_raw = load_file_local_first(
            path=self.raw_urls_folder, file_name=f"{self.urls_filename}.json"
        )
        print(f"Length of incoming urls: {len(scraper_urls_raw)}")
        self._run_scrapy_scraper(scraper_urls_raw)
        raw_xml = self._combine_xml_files_to_master()

        file_name = CONFIGS[self.scraper_type]["output_raw_xml_suffix"].replace(
            "{}", self.file_group
        )

        save_file_local_first(
            path=self.scraped_files_folder,
            file_name=file_name,
            data=raw_xml,
        )

    def _run_scrapy_scraper(self, scraper_urls_raw) -> None:

        if self.scraper_type in ["games", "ratings"]:
            process = CrawlerProcess(
                settings={
                    "LOG_LEVEL": "DEBUG",
                    "BOT_NAME": self.bot_scraper_name,
                    "ROBOTSTXT_OBEY": ROBOTSTXT_OBEY,
                    "DOWNLOAD_DELAY": 2,
                    "COOKIES_ENABLED": COOKIES_ENABLED,
                    "AUTOTHROTTLE_ENABLED": AUTOTHROTTLE_ENABLED,
                    "AUTOTHROTTLE_START_DELAY": AUTOTHROTTLE_START_DELAY,
                    "AUTOTHROTTLE_MAX_DELAY": AUTOTHROTTLE_MAX_DELAY,
                    "AUTOTHROTTLE_TARGET_CONCURRENCY": AUTOTHROTTLE_TARGET_CONCURRENCY,
                    "AUTOTHROTTLE_DEBUG": AUTOTHROTTLE_DEBUG,
                }
            )

            process.crawl(
                GameSpider,
                name="bgg_raw",
                scraper_urls_raw=scraper_urls_raw,
                save_file_path=self.scraped_files_folder,
                group=self.file_group,
            )

            process.start()

        if self.scraper_type == "users":
            process = CrawlerProcess(
                settings={
                    "LOG_LEVEL": "DEBUG",
                    "BOT_NAME": self.bot_scraper_name,
                    "ROBOTSTXT_OBEY": ROBOTSTXT_OBEY,
                    "DOWNLOAD_DELAY": 5,
                    "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
                    "COOKIES_ENABLED": COOKIES_ENABLED,
                    "AUTOTHROTTLE_ENABLED": AUTOTHROTTLE_ENABLED,
                    "AUTOTHROTTLE_START_DELAY": 3,
                    "AUTOTHROTTLE_MAX_DELAY": 60,
                    "AUTOTHROTTLE_TARGET_CONCURRENCY": 1,
                    "AUTOTHROTTLE_DEBUG": AUTOTHROTTLE_DEBUG,
                    "RANDOMIZE_DOWNLOAD_DELAY": True,
                }
            )

            process.crawl(
                UserSpider,
                name="bgg_users",
                scraper_urls_raw=scraper_urls_raw,
                save_file_path=self.scraped_files_folder,
                group=self.file_group,
            )

            process.start()

        # Testing section to see what happens after we are done with process.start()
        print("Completed with scraping process")

    def _combine_xml_files_to_master(self) -> str:
        """Combine the XML files into a single XML file"""

        print(f"\n\nCombining XML files for {self.file_group}")

        print(get_local_keys_based_on_env(self.scraped_files_folder))

        saved_files = [
            x
            for x in get_local_keys_based_on_env(self.scraped_files_folder)
            if "combined" not in x and ".gitkeep" not in x
        ]

        # Parse the first XML file to get the root and header
        tree = ET.parse(saved_files[0])
        root = tree.getroot()

        # Create a new root element for the combined XML
        combined_root = ET.Element(root.tag, root.attrib)

        # Iterate over each XML file
        for xml_file in saved_files:
            # Parse the XML file
            tree = ET.parse(xml_file)
            root = tree.getroot()

            if self.scraper_type == "users":
                user_name = xml_file.split("user_")[-1].split(".xml")[0]
                user_tag = ET.SubElement(combined_root, "username", value=user_name)

                # Append each <item> element to the new root
                for item in root.findall("item"):
                    user_tag.append(item)
            else:
                # Append each <item> element to the new root
                for item in root.findall("item"):
                    combined_root.append(item)

        # Create a new XML tree and write it to a new file
        combined_tree = ET.ElementTree(combined_root)

        # Get the root element from the ElementTree
        combined_root = combined_tree.getroot()

        xml_bytes = ET.tostring(combined_root, encoding="utf-8", xml_declaration=True)

        if IS_LOCAL and ENVIRONMENT == "dev":
            # remove the saved files
            for xml_file in saved_files:
                os.remove(xml_file)

        return xml_bytes


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "scraper_type",
        type=str,
        help="The type of scraper to run.  Current options are ['games', 'ratings', 'users']",
    )
    parser.add_argument(
        "urls_filename",
        type=str,
        help=f"The filename containing the urls to scrape.  Do not include the path.  Extension is optional but will be ignored.",
    )
    return parser.parse_args()


if __name__ == "__main__":

    args = parse_args()
    scraper_type = args.scraper_type
    urls_filename = args.urls_filename

    print(f"Running {scraper_type} scraper with urls from {urls_filename}")

    DataScraper(scraper_type, urls_filename).scraper_process_chain()
