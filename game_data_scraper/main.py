import argparse
import os
import sys
from datetime import datetime
from functools import partial

import scrapy
from scraper_config import SCRAPER_CONFIG
from scrapy.crawler import CrawlerProcess
from scrapy_settings import *

from config import DIRECTORY_CONFIGS
from utils.load_save import DataSaver, LocalLoader, LocalSaver, S3Loader, S3Saver
from utils.read_write import JSONReader, JSONWriter, XMLWriter

S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")
ENV = os.environ.get("ENV", "dev")


class BGGSpider(scrapy.Spider):
    """Spider to scrape BGG for game data"""

    def __init__(
        self,
        name: str,
        scraper_urls_raw: list[str],
        filename: str,
        saver: DataSaver,
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
        self.filename = filename
        self.saver = saver

    def start_requests(self):
        for i, url in enumerate(self.scraper_urls_raw):
            print(f"Starting URL {i}: {url}")
            save_response_with_index = partial(self._save_response, response_id=i)
            yield scrapy.Request(url=url, callback=save_response_with_index)

    def _save_response(self, response: scrapy.http.Response, response_id: int):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.saver.save_data(
            response.body, f"{self.filename}{response_id}_{timestamp}.xml"
        )


def set_vars_depending_on_scraper_type(scraper_type: str) -> tuple:
    """Set the variables depending on the scraper type"""
    json_urls_prefix = SCRAPER_CONFIG[scraper_type]["s3_location"]
    scrapy_bot_name = SCRAPER_CONFIG[scraper_type]["bot_name"]
    local_path = SCRAPER_CONFIG[scraper_type]["local_path"]
    scraped_games_save = SCRAPER_CONFIG[scraper_type]["save_subfolder"]

    return json_urls_prefix, scrapy_bot_name, local_path, scraped_games_save


def set_base_save_filename(filename: str, scraper_type: str) -> str:
    """Set the base filename for the saved files"""
    return f"{filename.split("_")[0]}_{scraper_type}_raw_"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "scraper_type",
        type=str,
        help="The type of scraper to run.  Current options are 'game' and 'user'",
    )
    parser.add_argument(
        "filename",
        type=str,
        help=f"The filename to process from path local_files/{DIRECTORY_CONFIGS['scraper_urls_raw_game']}, without a suffix",
    )
    return parser.parse_args()


if __name__ == "__main__":

    args = parse_args()
    scraper_type = args.scraper_type
    filename = args.filename

    json_urls_prefix, scrapy_bot_name, local_path, scraped_games_save = (
        set_vars_depending_on_scraper_type(scraper_type)
    )

    print(filename)

    process = CrawlerProcess(
        settings={
            "LOG_LEVEL": "DEBUG",
            "BOT_NAME": scrapy_bot_name,
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

    # get file from local if dev, else from S3
    if os.path.exists(f"{local_path}/{filename}.json"):
        scraper_urls_raw = LocalLoader(JSONReader(), local_path).load_data(
            f"{filename}.json"
        )
    else:
        scraper_urls_raw = S3Loader(
            JSONReader(), f"s3://{S3_SCRAPER_BUCKET}/{json_urls_prefix}"
        ).load_data(f"{filename}.json")

    if ENV == "dev":
        if not os.path.exists(f"{local_path}/{filename}.json"):
            LocalSaver(
                JSONWriter(local_path),
            ).save_data(scraper_urls_raw, f"{filename}.json")
        scraper_urls_raw = scraper_urls_raw[:1]
        data_saver = LocalSaver(XMLWriter(), scraped_games_save)
        print(scraper_urls_raw)
    elif ENV == "prod":
        data_saver = S3Saver(XMLWriter(), scraped_games_save)
    else:
        raise ValueError("ENV must be either 'dev' or 'prod'")

    filename = set_base_save_filename(filename, scraper_type)

    process.crawl(
        BGGSpider,
        name="bgg_raw",
        scraper_urls_raw=scraper_urls_raw,
        filename=filename,
        saver=data_saver,
    )

    process.start()
