import json
from datetime import datetime

import scrapy


class BggSpider(scrapy.Spider):
    name = "bgg_ratings"

    def __init__(self, group=None):
        self.group = group
        self.url_num = 1

    def start_requests(self):
        with open("data_store/data_dirty/scraper_urls_ratings.json") as json_file:
            scraper_urls_ratings = json.load(json_file)

        start_urls = scraper_urls_ratings[self.group]

        len_urls = len(start_urls)
        print(f"{self.group} has {len_urls} urls to scrape.")

        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

        self.url_num += 1

    def parse(self, response):
        page = response.url
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"data_store/data_dirty/pulled_ratings/ratings_{str(self.group)}_{self.url_num}.xml"
        with open(filename, "wb") as f:
            f.write(response.body)
