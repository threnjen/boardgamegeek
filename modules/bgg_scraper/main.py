import argparse
import os
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from functools import partial

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy_settings import *

from config import CONFIGS
from utils.local_file_handler import LocalFileHandler
from utils.processing_functions import load_file_local_first, save_file_local_first
from utils.s3_file_handler import S3FileHandler

S3_SCRAPER_BUCKET = CONFIGS["s3_scraper_bucket"]
IS_LOCAL = True if os.environ.get("IS_LOCAL", "False").lower() == "true" else False
ENVIRONMENT = os.environ.get("TF_VAR_RESOURCE_ENV" "dev")
WORKING_DIR = f"data/{ENVIRONMENT}"


class GameSpider(scrapy.Spider):
    """Spider to scrape BGG for game data"""

    def __init__(
        self,
        name: str,
        scraper_urls_raw: list[str],
        save_file_path: str,
        group: str,
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
        self.group = group
        self.s3_file_handler = S3FileHandler()
        self.local_file_handler = LocalFileHandler()

    def start_requests(self):
        for i, url in enumerate(self.scraper_urls_raw):

            # check S3 for existing data
            if self.s3_file_handler.check_file_exists(
                file_path=f"{WORKING_DIR}{self.save_file_path}/{self.group}_{i}.xml"
            ):
                self.logger.info(f"ID {self.group}_{i} already exists. Skipping...")
                continue

            print(f"Starting URL {i}: {url}")
            save_response_with_index = partial(self._save_response, response_id=i)
            yield scrapy.Request(url=url, callback=save_response_with_index)

    def _save_response(self, response: scrapy.http.Response, response_id: int):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        save_file_local_first(
            path=self.save_file_path,
            file_name=f"{self.group}_{response_id}.xml",
            data=response.body,
        )


class UserSpider(scrapy.Spider):
    """Spider to scrape BGG for game data"""

    def __init__(
        self,
        name: str,
        scraper_urls_raw: list[str],
        save_file_path: str,
        group: str,
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
        self.group = group
        self.s3_file_handler = S3FileHandler()
        self.local_file_handler = LocalFileHandler()

    def start_requests(self):
        for self.group_num, url in enumerate(self.scraper_urls_raw):
            user_id = url.split("username=")[-1].split("&rated")[0]

            # check S3 for existing user data
            if self.s3_file_handler.check_file_exists(
                file_path=f"{WORKING_DIR}{self.save_file_path}/user_{user_id}.xml"
            ):
                self.logger.info(f"User {user_id} already exists. Skipping...")
                continue

            self.logger.info(f"Starting URL {self.group_num}: {url}")
            yield scrapy.Request(
                url=url,
                meta={"group_num": self.group_num},
                dont_filter=True,
                callback=self.parse,
            )

    def parse(self, response):
        if response.status == 429:
            self.logger.info(
                "Received 429 status code. Waiting significant time before retry..."
            )
            time.sleep(45)
            yield scrapy.Request(
                url=response.url,
                callback=self.parse,
                dont_filter=True,
                meta=response.meta,  # Preserve meta information
            )
        if (
            "Your request for this collection has been accepted"
            in response.body.decode("utf-8")
        ):
            self.logger.info("Received 'Request accepted' message. Retrying...")
            time.sleep(5)
            yield scrapy.Request(
                url=response.url,
                callback=self.parse,
                dont_filter=True,
                meta=response.meta,  # Preserve meta information
            )
            return

        # Process the valid response
        self._save_response(response, response.url)

    def _save_response(self, response: scrapy.http.Response, url: str):
        user_id = url.split("username=")[-1].split("&rated")[0]
        file_path = f"{WORKING_DIR}{self.save_file_path}/user_{user_id}.xml"
        save_file_local_first(
            path=self.save_file_path,
            file_name=f"user_{user_id}.xml",
            data=response.body,
        )
        self.logger.info(f"Response saved to {file_path}")


class DataScraper:

    def __init__(self, data_type: str, urls_filename: str) -> None:
        self.file_group = urls_filename.split("_")[0]
        self.urls_filename = urls_filename.split(".")[0]
        self.bot_scraper_name = CONFIGS[data_type]["scrapy_bot_name"]
        self.raw_urls_folder = CONFIGS[data_type]["raw_urls_directory"]
        self.scraped_files_folder = CONFIGS[data_type]["output_xml_directory"]
        self.data_type = data_type

    def scraper_process_chain(self):
        scraper_urls_raw = load_file_local_first(
            path=self.raw_urls_folder, file_name=f"{self.urls_filename}.json"
        )
        print(f"Length of incoming urls: {len(scraper_urls_raw)}")
        self._run_scrapy_scraper(scraper_urls_raw)

    def _run_scrapy_scraper(self, scraper_urls_raw) -> None:

        if self.data_type in ["games", "ratings"]:
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

        if self.data_type == "users":
            process = CrawlerProcess(
                settings={
                    "LOG_LEVEL": "DEBUG",
                    "BOT_NAME": self.bot_scraper_name,
                    "ROBOTSTXT_OBEY": ROBOTSTXT_OBEY,
                    "DOWNLOAD_DELAY": 5,
                    "CONCURRENT_REQUESTS_PER_DOMAIN": 4,
                    "COOKIES_ENABLED": COOKIES_ENABLED,
                    "AUTOTHROTTLE_ENABLED": AUTOTHROTTLE_ENABLED,
                    "AUTOTHROTTLE_START_DELAY": 3,
                    "AUTOTHROTTLE_MAX_DELAY": 60,
                    "AUTOTHROTTLE_TARGET_CONCURRENCY": 4,
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


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "data_type",
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
    data_type = args.data_type
    urls_filename = args.urls_filename

    print(f"Running {data_type} scraper with urls from {urls_filename}")

    DataScraper(data_type, urls_filename).scraper_process_chain()
