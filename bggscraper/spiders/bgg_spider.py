import scrapy
from datetime import datetime
import json

class BggSpider(scrapy.Spider):

  name="bgg_ratings" 
  
  def start_requests(self):
    
    group = self.group
    print(group)
    
    with open('data_dirty/scraper_urls_ratings.json') as json_file:
      scraper_urls_ratings = json.load(json_file)
       
    start_urls = scraper_urls_ratings[group]
    
    for url in start_urls:
      yield scrapy.Request(url=url, callback=self.parse)    
    
  def parse(self, response):
         
    page = response.url
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f'data_dirty/pulled_ratings/ratings_{str(self.group)}_{timestamp}.xml'
    with open (filename, 'wb') as f:
      f.write(response.body)
    self.log("saved test file")
    pass

  