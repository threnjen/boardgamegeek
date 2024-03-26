import scrapy
import time
import boto3
import json
from datetime import datetime
import boto3
import os

IS_LOCAL = os.environ.get("IS_LOCAL", True)
s3_client = boto3.client("s3")


class BggSpider(scrapy.Spider):
    name = "bgg_raw"

    def __init__(self, scraper_urls_raw=None):
        scraper_urls_raw = scraper_urls_raw
        self.url_num = 1

    def start_requests(self):
        if IS_LOCAL:
            with open("data_dirty/scraper_urls_raw.json") as json_file:
                scraper_urls_raw = json.load(json_file)
        else:
            result = s3_client.get_object(
                Bucket="boardgamegeek-scraper", Key="scraper_urls_raw.json"
            )
            scraper_urls_raw = json.load(result["Body"])

        print(len(scraper_urls_raw))

        for url in scraper_urls_raw:
            print(f"Starting URL {self.url_num}")
            yield scrapy.Request(url=url, callback=self.parse)

        self.url_num += 1

    def parse(self, response):
        page = response.url
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"data_dirty/pulled_games/raw_{self.url_num}_{timestamp}.xml"
        if not IS_LOCAL:
            response = s3_client.put_object(
                Body=response.body,
                Bucket="boardgamegeek-scraper",
                key=filename,
            )
        with open(filename, "wb") as f:
            f.write(response.body)
