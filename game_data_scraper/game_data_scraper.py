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

S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")
JSON_URLS_PREFIX = os.environ.get("JSON_URLS_PREFIX")
LOCAL_SCRAPER_PATH = os.environ.get("LOCAL_SCRAPER_PATH", ".")
ENV = os.environ.get("ENV", "dev")


class BGGSpider(scrapy.Spider):
    """Spider to scrape BGG for game data"""

    def __init__(self, name: str, scraper_urls_raw: list[str], filename: str):
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
        self.filename = f'file_{filename.split("_")[-1]}'
        print("Completed init")

    def start_requests(self):
        for i, url in enumerate(self.scraper_urls_raw):
            print(f"Starting URL {i}: {url}")
            save_response_with_index = partial(self._save_response, response_id=i)
            yield scrapy.Request(url=url, callback=save_response_with_index)

    def _save_response(self, response: scrapy.http.Response, response_id: int):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        save_subfolder = (
            f"{LOCAL_SCRAPER_PATH}/scraped_games" if ENV != "prod" else "scraped_games"
        )
        save_filename = f"{self.filename}_raw_xml_{response_id}_{timestamp}.xml"
        full_local_path = f"{save_subfolder}/{save_filename}"
        print(full_local_path)

        with open(full_local_path, "wb") as f:
            f.write(response.body)

        if ENV == "prod":
            s3_client = boto3.client("s3")
            s3_client.upload_file(
                full_local_path,
                S3_SCRAPER_BUCKET,
                f"data_dirty/{save_subfolder}/{save_filename}",
            )


if __name__ == "__main__":

    filename = sys.argv[1]
    print(filename)

    # get file from local if dev, else from S3

    if ENV == "dev":
        scraper_urls_raw = json.load(
            open(f"data_store/local_files/scraper_urls_raw/{filename}.json")
        )
    else:
        wr.s3.download(
            path=f"s3://{S3_SCRAPER_BUCKET}/{JSON_URLS_PREFIX}/{filename}.json",
            local_file=f"{filename}.json",
        )
        scraper_urls_raw = json.load(open(f"{filename}.json"))

    process = CrawlerProcess(
        settings={
            "LOG_LEVEL": "DEBUG",
            "BOT_NAME": BOT_NAME,
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

    process.crawl(
        BGGSpider,
        name="bgg_raw",
        scraper_urls_raw=scraper_urls_raw,
        filename=filename,
    )
    process.start()
