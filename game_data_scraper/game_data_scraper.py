import pandas as pd

pd.set_option("display.max_columns", None)
import numpy as np
from bs4 import BeautifulSoup
import requests
import regex as re
import time
import json
import os
import gc
import scrapy
import boto3
from lxml import etree
from datetime import datetime
import subprocess

# ignore warnings (gets rid of Pandas copy warnings)
import warnings

warnings.filterwarnings("ignore")

import os

def scrape_urls_file():

    with open("data_store/data_dirty/scraper_urls_raw.json", "w") as convert_file:
        convert_file.write(json.dumps(scraper_urls_raw))

    subprocess.call("scrapy crawl bgg_raw")


if __name__ == "__main__":
    scrape_urls_file()
