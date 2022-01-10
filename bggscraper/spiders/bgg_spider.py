import scrapy
import time
import json

class BggSpider(scrapy.Spider):

  name="bgg" 
  
  def start_requests(self):
    
    group = self.group
    print(group)
    
    with open('data_cleaned/scraper_urls_ratings.json') as json_file:
      scraper_urls_ratings = json.load(json_file)
       
    start_urls = scraper_urls_ratings[group]
    
    for url in start_urls:
      yield scrapy.Request(url=url, callback=self.parse)    
    
  def parse(self, response):
         
    page = response.url
    timestamp = time.time()
    filename = 'data_dirty/pulled_ratings/ratings_{}_{}.xml'.format(str(self.group), str(timestamp))
    with open (filename, 'wb') as f:
      f.write(response.body)
    self.log("saved test file")
    pass

  