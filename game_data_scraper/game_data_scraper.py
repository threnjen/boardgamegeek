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


def read_csv_from_s3(bucket="boardgamegeek-scraper", key="boardgames_ranks.csv"):
    """Reads in the csv from S3"""

    # read in the csv from S3
    # s3_client = boto3.client('s3')
    # obj = s3_client.get_object(Bucket=bucket, Key=key)
    # games = pd.read_csv(obj['Body'].read(), low_memory=False)

    games = pd.read_csv("boardgames_ranks.csv", low_memory=False)

    # return dataframe
    return games


def write_json_to_s3(data, bucket="boardgamegeek-scraper", key="scraper_urls_raw.json"):
    """Writes a json to S3"""

    # write the json to S3
    s3_client = boto3.client("s3")
    s3_client.put_object(Body=json.dumps(data), Bucket=bucket, Key=key)


def generate_raw_urls(game_ids):

    game_block = 500

    start_position = 0
    end_position = game_block
    urls_list = []

    while start_position < (len(game_ids) + 1):

        ##### File Setup Section #####

        # print start and end positions
        print(f"Getting items {str(start_position+1)} through {str(end_position)}")

        # get list of game ids to grab
        grab_list = game_ids[start_position:end_position]

        # piece together target string of game ids for BGG
        targets = ""
        for item in grab_list:
            targets += f"{str(item)},"

        # establish path with targets and current page
        path = f"https://www.boardgamegeek.com/xmlapi2/thing?id={targets}&stats=1&type=boardgame"
        urls_list.append(path)

        start_position += game_block
        end_position += game_block

    return urls_list


def scrape_urls_file():

    game_ids_df = read_csv_from_s3(key="boardgames_ranks.csv")
    game_ids = game_ids_df["id"].astype(int).to_list()

    scraper_urls_raw = generate_raw_urls(game_ids)

    with open("data_store/data_dirty/scraper_urls_raw.json", "w") as convert_file:
        convert_file.write(json.dumps(scraper_urls_raw))

    subprocess.call("scrapy crawl bgg_raw")


if __name__ == "__main__":
    scrape_urls_file()
