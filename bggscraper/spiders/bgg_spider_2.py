import scrapy
import time
import json
from datetime import datetime


class BggSpider(scrapy.Spider):
    name = "bgg_raw"

    def start_requests(self):
        with open("data_dirty/scraper_urls_raw.json") as json_file:
            scraper_urls_raw = json.load(json_file)

        for url in scraper_urls_raw:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        page = response.url
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"data_dirty/pulled_games/raw_{timestamp}.xml"
        with open(filename, "wb") as f:
            f.write(response.body)
