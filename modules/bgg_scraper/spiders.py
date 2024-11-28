import os
import time
from datetime import datetime
from functools import partial

import scrapy
from scrapy_settings import *

from config import CONFIGS
from utils.s3_file_handler import S3FileHandler
from utils.local_file_handler import LocalFileHandler
from utils.processing_functions import (
    load_file_local_first,
    save_file_local_first,
)

S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")
IS_LOCAL = True if os.environ.get("IS_LOCAL", "False").lower() == "true" else False
ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
WORKING_DIR = (
    CONFIGS["dev_directory"] if ENVIRONMENT == "dev" else CONFIGS["prod_directory"]
)


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

    def start_requests(self):
        for i, url in enumerate(self.scraper_urls_raw):
            print(f"Starting URL {i}: {url}")
            save_response_with_index = partial(self._save_response, response_id=i)
            yield scrapy.Request(url=url, callback=save_response_with_index)

    def _save_response(self, response: scrapy.http.Response, response_id: int):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        save_file_local_first(
            path=self.save_file_path,
            file_name=f"{self.group}_{response_id}_{timestamp}.xml",
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

    def download_from_s3(self, file_path: str):
        if IS_LOCAL:
            return load_file_local_first(path=self.save_file_path, file_name=file_path)
        else:
            file = self.s3_file_handler.load_xml(f"{WORKING_DIR}{file_path}")
            self.local_file_handler.save_xml(
                file_path=f"{WORKING_DIR}{self.save_file_path}/{file_path}", data=file
            )

    def start_requests(self):
        for self.group_num, url in enumerate(self.scraper_urls_raw):
            user_id = url.split("username=")[-1].split("&rated")[0]

            # check S3 for existing user data
            if self.s3_file_handler.check_file_exists(
                file_path=f"{WORKING_DIR}{self.save_file_path}/user_{user_id}.xml"
            ):
                self.download_from_s3()
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
