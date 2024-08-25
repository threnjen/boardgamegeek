from functools import partial
import scrapy
from datetime import datetime
import json
import os
import sys
import boto3
import awswrangler as wr
from scrapy.crawler import CrawlerProcess
from scrapy_settings import *
from scraper_config import SCRAPER_CONFIG

S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")
ENV = os.environ.get("ENV", "dev")


class BGGSpider(scrapy.Spider):
    """Spider to scrape BGG for game data"""

    def __init__(
        self,
        name: str,
        scraper_urls_raw: list[str],
        filename: str,
        local_save_path: str,
        scraper_type: str,
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
        self.local_save_path = local_save_path
        self.scraper_type = scraper_type
        print("Completed init")

    def set_filename(self):
        filename = f'gameset{self.filename.split("_")[-1].split(".")[0]}' if self.scraper_type == "game" else self.filename.split("_")[0].split(".")[0]
        filename = f"{filename}_{self.scraper_type}_raw_"
        return filename

    def start_requests(self):
        for i, url in enumerate(self.scraper_urls_raw):
            print(f"Starting URL {i}: {url}")
            save_response_with_index = partial(self._save_response, response_id=i)
            yield scrapy.Request(url=url, callback=save_response_with_index)

    def _save_response(self, response: scrapy.http.Response, response_id: int):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        save_filename = f"{self.set_filename()}{response_id}_{timestamp}.xml"
        full_local_path = f"{self.local_save_path}/{save_filename}"
        print(full_local_path)

        with open(full_local_path, "wb") as f:
            f.write(response.body)

        if ENV == "prod":
            s3_client = boto3.client("s3")
            s3_client.upload_file(
                full_local_path,
                S3_SCRAPER_BUCKET,
                f"data_dirty/{self.local_save_path}/{save_filename}",
            )


def set_vars_depending_on_scraper_type(scraper_type):
    json_urls_prefix = SCRAPER_CONFIG[scraper_type]["s3_location"]
    scrapy_bot_name = SCRAPER_CONFIG[scraper_type]["bot_name"]
    local_path = SCRAPER_CONFIG[scraper_type]["local_path"]
    scraped_games_save = SCRAPER_CONFIG[scraper_type]["local_subfolder"]

    return json_urls_prefix, scrapy_bot_name, local_path, scraped_games_save


if __name__ == "__main__":

    scraper_type = sys.argv[1]
    filename = sys.argv[2]

    json_urls_prefix, scrapy_bot_name, local_path, scraped_games_save = (
        set_vars_depending_on_scraper_type(scraper_type)
    )

    print(filename)

    # get file from local if dev, else from S3

    if ENV == "dev":
        scraper_urls_raw = json.load(open(f"{local_path}/{filename}.json"))
    else:
        wr.s3.download(
            path=f"s3://{S3_SCRAPER_BUCKET}/{json_urls_prefix}/{filename}.json",
            local_file=f"{local_path}/{filename}.json",
        )
        scraper_urls_raw = json.load(open(f"{local_path}/{filename}.json"))

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

    if ENV != "prod":
        scraper_urls_raw = scraper_urls_raw[:1]
        print(scraper_urls_raw)

    process.crawl(
        BGGSpider,
        name="bgg_raw",
        scraper_urls_raw=scraper_urls_raw,
        filename=filename,
        local_save_path=scraped_games_save,
        scraper_type=scraper_type,
    )

    process.start()
