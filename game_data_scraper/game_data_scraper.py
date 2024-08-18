from functools import partial
import scrapy
from datetime import datetime
import json
import os
import sys
import boto3
import awswrangler as wr
from scrapy.crawler import CrawlerProcess
from config import S3_SCRAPER_BUCKET, JSON_URLS_PREFIX
from scrapy_settings import SCRAPY_SETTINGS


class BGGSpider(scrapy.Spider):
    """Spider to scrape BGG for game data"""

    def __init__(self, name: str, scraper_urls_raw: list[str]):
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
        print("Completed init")

    @classmethod
    def update_settings(cls, settings):
        super().update_settings(settings)
        for setting in SCRAPY_SETTINGS:
            settings.set(setting, SCRAPY_SETTINGS[setting], priority="spider")

    def start_requests(self):
        for i, url in enumerate(self.scraper_urls_raw):
            print(f"Starting URL {i}: {url}")
            save_response_with_index = partial(self._save_response, response_id=i)
            yield scrapy.Request(url=url, callback=save_response_with_index)

    def _save_response(self, response: scrapy.http.Response, response_id: int):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        save_subfolder = "data_dirty/scraped_games"
        full_local_path = f"data_store/{save_subfolder}/"
        save_filename = f"raw_bgg_xml_{response_id}_{timestamp}.xml"

        os.makedirs(full_local_path, exist_ok=True)

        with open(f"{full_local_path}/{save_filename}", "wb") as f:
            f.write(response.body)

        if ENV == "prod":
            s3_client = boto3.client("s3")
            s3_client.upload_file(
                f"{full_local_path}/{save_filename}",
                S3_SCRAPER_BUCKET,
                f"{save_subfolder}/{save_filename}",
            )


if __name__ == "__main__":

    filename = sys.argv[1]
    local_file = f"data_store/local_files/scraper_urls_raw/{filename}.json"

    # get file from local if dev, else from S3
    ENV = os.environ.get("ENV", "dev")
    if ENV == "dev":
        scraper_urls_raw = json.load(open(local_file))
    else:
        wr.s3.download(
            path=f"s3://{S3_SCRAPER_BUCKET}/{JSON_URLS_PREFIX}/{filename}.json",
            local_file=local_file,
        )
        scraper_urls_raw = json.load(open(local_file))

    process = CrawlerProcess(
        settings={
            "LOG_LEVEL": "DEBUG",
            # other Scrapy settings if needed
        }
    )

    if ENV != "prod":
        scraper_urls_raw = scraper_urls_raw[:1]

    process.crawl(
        BGGSpider,
        name="bgg_raw",
        scraper_urls_raw=scraper_urls_raw,
    )
    process.start()
