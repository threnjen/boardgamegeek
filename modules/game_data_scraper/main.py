import argparse
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from functools import partial

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy_settings import *

from modules.config import CONFIGS
from utils.file_handler import FileHandler
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


class BGGSpider(scrapy.Spider):
    """Spider to scrape BGG for game data"""

    def __init__(
        self,
        name: str,
        scraper_urls_raw: list[str],
        save_file_path: str,
        group: str,
        file_handler: FileHandler,
    ):
        """
        Parameters:
        name: str
            The name of the spider
        save_folder: str
            The folder to save the data to
        scraper_urls_raw: list[str]
            The urls to scrape
        """
        self.name = name
        super().__init__()
        self.scraper_urls_raw = scraper_urls_raw
        self.save_file_path = save_file_path
        self.file_handler = file_handler
        self.group = group

    def start_requests(self):
        for i, url in enumerate(self.scraper_urls_raw):
            print(f"Starting URL {i}: {url}")
            save_response_with_index = partial(self._save_response, response_id=i)
            yield scrapy.Request(url=url, callback=save_response_with_index)

    def _save_response(self, response: scrapy.http.Response, response_id: int):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        self.file_handler.save_file(
            file_path=f"{WORKING_DIR}{self.save_file_path}/{self.group}_{response_id}_{timestamp}.xml",
            data=response.body,
        )


class GameScraper:

    def __init__(self, scraper_type: str, urls_filename: str) -> None:
        self.file_group = urls_filename.split("_")[0]
        self.urls_filename = urls_filename.split(".")[0]
        self.bot_scraper_name = CONFIGS[scraper_type]["scrapy_bot_name"]
        self.raw_urls_folder = CONFIGS[scraper_type]["raw_urls_directory"]
        self.scraped_games_folder = CONFIGS[scraper_type]["output_xml_directory"]
        self.scraper_type = scraper_type

    def run_game_scraper_processes(self):
        scraper_urls_raw = load_file_local_first(
            path=self.raw_urls_folder, file_name=f"{self.urls_filename}.json"
        )
        self._run_scrapy_scraper(scraper_urls_raw)
        raw_xml = self._combine_xml_files_to_master()

        file_name = CONFIGS[self.scraper_type]["output_raw_xml_suffix"].replace(
            "{}", self.file_group
        )

        save_file_local_first(
            path=self.scraped_games_folder,
            file_name=file_name,
            data=raw_xml,
        )

    def _run_scrapy_scraper(self, scraper_urls_raw) -> None:
        process = CrawlerProcess(
            settings={
                "LOG_LEVEL": "DEBUG",
                "BOT_NAME": self.bot_scraper_name,
                "ROBOTSTXT_OBEY": ROBOTSTXT_OBEY,
                "DOWNLOAD_DELAY": DOWNLOAD_DELAY,
                "COOKIES_ENABLED": COOKIES_ENABLED,
                "AUTOTHROTTLE_ENABLED": AUTOTHROTTLE_ENABLED,
                "AUTOTHROTTLE_START_DELAY": AUTOTHROTTLE_START_DELAY,
                "AUTOTHROTTLE_MAX_DELAY": AUTOTHROTTLE_MAX_DELAY,
                "AUTOTHROTTLE_TARGET_CONCURRENCY": AUTOTHROTTLE_TARGET_CONCURRENCY,
                "AUTOTHROTTLE_DEBUG": AUTOTHROTTLE_DEBUG,
            }
        )

        process.crawl(
            BGGSpider,
            name="bgg_raw",
            scraper_urls_raw=scraper_urls_raw,
            save_file_path=self.scraped_games_folder,
            group=self.file_group,
            file_handler=LocalFileHandler(),
        )

        process.start()

        # Testing section to see what happens after we are done with process.start()
        print("Completed with scraping process")

    def _combine_xml_files_to_master(self) -> str:
        """Combine the XML files into a single XML file"""

        print(f"Combining XML files for {self.file_group}")

        print(get_local_keys_based_on_env(self.scraped_games_folder))

        saved_files = [
            x
            for x in get_local_keys_based_on_env(self.scraped_games_folder)
            if self.file_group in x and "combined" not in x
        ]
        print(saved_files)

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

            # Append each <item> element to the new root
            for item in root.findall("item"):
                combined_root.append(item)

        # Create a new XML tree and write it to a new file
        combined_tree = ET.ElementTree(combined_root)

        # Get the root element from the ElementTree
        combined_root = combined_tree.getroot()

        xml_bytes = ET.tostring(combined_root, encoding="utf-8", xml_declaration=True)

        if ENVIRONMENT == "dev":
            # remove the saved files
            for xml_file in saved_files:
                os.remove(xml_file)

        return xml_bytes


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "scraper_type",
        type=str,
        help="The type of scraper to run.  Current options are 'game' and 'user'",
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

    GameScraper(scraper_type, urls_filename).run_game_scraper_processes()
