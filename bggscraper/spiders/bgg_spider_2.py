import scrapy
import time
import json
from datetime import datetime


class BggSpider(scrapy.Spider):
    name = "bgg_raw"

    def __init__(self, scraper_urls_raw=None):
        self.scraper_urls_raw = scraper_urls_raw
        self.url_num = 1

    def start_requests(self):
        with open("data_dirty/scraper_urls_raw.json") as json_file:
            self.scraper_urls_raw = json.load(json_file)

        print(len(self.scraper_urls_raw))

        for url in self.scraper_urls_raw:
            print(f"Starting URL {self.url_num}")
            yield scrapy.Request(url=url, callback=self.parse)

        self.url_num += 1

    def parse(self, response):
        page = response.url
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"data_dirty/pulled_games/raw_{self.url_num}_{timestamp}.xml"
        with open(filename, "wb") as f:
            f.write(response.body)
