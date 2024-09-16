import argparse
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from functools import partial

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy_settings import *

from config import CONFIGS
from utils.file_handler import FileHandler
from utils.local_file_handler import LocalFileHandler
from utils.s3_file_handler import S3FileHandler

S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")
IS_LOCAL = True if os.environ.get("IS_LOCAL", "False") == "True" else False
ENV = os.environ.get("ENV", "dev")


class BGGSpider(scrapy.Spider):
    """Spider to scrape BGG for game data"""

    def __init__(
        self,
        name: str,
        scraper_urls_raw: list[str],
        save_file_path: str,
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

    def start_requests(self):
        for i, url in enumerate(self.scraper_urls_raw):
            print(f"Starting URL {i}: {url}")
            save_response_with_index = partial(self._save_response, response_id=i)
            yield scrapy.Request(url=url, callback=save_response_with_index)

    def _save_response(self, response: scrapy.http.Response, response_id: int):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.file_handler.save_file(
            file_path=f"{self.save_file_path}{response_id}_{timestamp}.xml",
            data=response.body,
        )


class GameScraper:

    def __init__(self, scraper_type: str, urls_filename: str) -> None:
        self.file_group = urls_filename.split("_")[0]
        self.urls_filename = urls_filename.split(".")[0]
        self.configs = CONFIGS[scraper_type]
        self.scraped_games_xml_folder = self.configs["output_xml_directory"]
        self.raw_urls_folder = self.configs["raw_urls_directory"]
        self.scraper_type = scraper_type

    def run_game_scraper_processes(self):
        scraper_urls_raw = self._load_scraper_urls()
        self._run_scrapy_scraper(scraper_urls_raw)
        raw_xml = self._combine_xml_files_to_master()
        self._write_combined_xml_file(
            raw_xml,
            combined_xml_filename=f"combined_{self.file_group}_{self.scraper_type}_raw.xml",
        )

    def _load_scraper_urls(self) -> list[str]:
        # get file from local if dev, else from S3
        filepath = f"{self.raw_urls_folder}/{self.urls_filename}.json"
        if os.path.exists(filepath):
            scraper_urls_raw = LocalFileHandler().load_file(filepath)
        else:
            print(f"File {filepath} not found.  Attempting to load from S3.")
            scraper_urls_raw = S3FileHandler().load_file(filepath)

        if ENV == "dev":
            scraper_urls_raw = scraper_urls_raw[:1]
            print(scraper_urls_raw)

        return scraper_urls_raw

    def _run_scrapy_scraper(self, scraper_urls_raw) -> None:
        process = CrawlerProcess(
            settings={
                "LOG_LEVEL": "DEBUG",
                "BOT_NAME": self.configs["scrapy_bot_name"],
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
            save_file_path=f"{self.scraped_games_xml_folder}/{self.urls_filename}",
            file_handler=LocalFileHandler(),
        )

        process.start()

        # Testing section to see what happens after we are done with process.start()
        print("Completed with scraping process")

    def _combine_xml_files_to_master(self) -> str:
        """Combine the XML files into a single XML file"""

        print(f"Combining XML files for {self.file_group}")

        saved_files = [
            f"{self.scraped_games_xml_folder}/{file_name}"
            for file_name in os.listdir(self.scraped_games_xml_folder)
            if self.file_group in file_name and "master" not in file_name
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

            # Append each <item> element to the new root
            for item in root.findall("item"):
                combined_root.append(item)

        # Create a new XML tree and write it to a new file
        combined_tree = ET.ElementTree(combined_root)

        # Get the root element from the ElementTree
        combined_root = combined_tree.getroot()

        xml_bytes = ET.tostring(combined_root, encoding="utf-8", xml_declaration=True)

        if ENV == "dev":
            # remove the saved files
            for xml_file in saved_files:
                os.remove(xml_file)

        return xml_bytes

    def _write_combined_xml_file(self, xml: bytes, combined_xml_filename=str) -> None:

        LocalFileHandler().save_file(
            file_path=f"test/{self.scraped_games_xml_folder}/{combined_xml_filename}",
            data=xml,
        )

        s3_path = (
            self.scraped_games_xml_folder
            if ENV == "prod"
            else f"test/{self.scraped_games_xml_folder}"
        )
        S3FileHandler().save_file(
            file_path=f"{s3_path}/{combined_xml_filename}", data=xml
        )


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
