import json
import math
import os

import awswrangler as wr
import boto3
import pandas as pd

from config import CONFIGS
from utils.local_file_handler import LocalFileHandler
from utils.s3_file_handler import S3FileHandler

ENV = os.environ.get("ENV", "dev")
S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")
CONFIGS = CONFIGS["game"]
url_block_size = 20
number_url_files = 30


def generate_raw_urls(game_ids: list[str]):
    """Generate the raw urls for the scraper"""
    targets = [
        game_ids[i : i + url_block_size]
        for i in range(0, len(game_ids), url_block_size)
    ]
    print(f"Generated {len(targets)} URLS with block size {url_block_size}")

    return [
        f"https://www.boardgamegeek.com/xmlapi2/thing?id={','.join(block)}&stats=1&type=boardgame"
        for block in targets
    ]


def lambda_handler(event, context):
    """Generate the raw URLs for the game scraper
    This function will read the game ids from the local csv file or S3
    and generate the raw URLs for the game scraper. The URLs
    will be split into blocks and saved to S3 for the scraper
    to pick up.
    """

    try:
        print("Reading the file locally")
        df = LocalFileHandler().load_csv("data/boardgames_ranks.csv")
    except:
        print("Reading the file from S3")
        df = S3FileHandler().load_csv(file_path="boardgames_ranks.csv")

    game_ids = df["id"].astype(str).to_list()
    print(f"Number of game ids: {len(game_ids)}")

    scraper_urls_raw = generate_raw_urls(game_ids)

    print(len(scraper_urls_raw))
    url_block_size = math.ceil(len(scraper_urls_raw) / number_url_files)
    print(f"URL block size: {url_block_size}")

    for i in range(number_url_files):
        print(f"Saving block size {i * url_block_size} : {(i + 1) * url_block_size}")

        scraper_urls_set = scraper_urls_raw[
            i * url_block_size : (i + 1) * url_block_size
        ]
        S3FileHandler().save_json(
            file_path=f"{CONFIGS['raw_urls_directory']}/group{i+1}_game_scraper_urls_raw.json",
            data=scraper_urls_set,
        )
        LocalFileHandler().save_json(
            file_path=f"data/{CONFIGS['raw_urls_directory']}/group{i+1}_game_scraper_urls_raw.json",
            data=scraper_urls_set,
        )


if __name__ == "__main__":
    lambda_handler(None, None)
