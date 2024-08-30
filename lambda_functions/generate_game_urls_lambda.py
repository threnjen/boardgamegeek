import json
import math
import os

import awswrangler as wr
import boto3
import pandas as pd

from config import CONFIGS

ENV = os.environ.get("ENV", "dev")
S3_SCRAPER_BUCKET = CONFIGS["s3_scraper_bucket"]
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
        df = pd.read_csv("local_data/boardgames_ranks.csv", low_memory=False)
    except:
        print("Reading the file from S3")
        df = wr.s3.read_csv(f"s3://{S3_SCRAPER_BUCKET}/boardgames_ranks.csv")

    game_ids = df["id"].astype(str).to_list()
    print(f"Number of game ids: {len(game_ids)}")

    scraper_urls_raw = generate_raw_urls(game_ids)

    print(len(scraper_urls_raw))
    url_block_size = math.ceil(len(scraper_urls_raw) / number_url_files)
    print(f"URL block size: {url_block_size}")

    local_path = (
        f"local_data/{CONFIGS['raw_urls_directory']}" if ENV != "prod" else "/tmp"
    )

    for i in range(number_url_files):
        print(f"Saving block size {i * url_block_size} : {(i + 1) * url_block_size}")
        with open(
            f"{local_path}/group{i+1}_game_scraper_urls_raw.json", "w"
        ) as convert_file:
            convert_file.write(
                json.dumps(
                    scraper_urls_raw[i * url_block_size : (i + 1) * url_block_size]
                )
            )
        s3_client = boto3.client("s3")
        s3_client.upload_file(
            f"{local_path}/group{i+1}_game_scraper_urls_raw.json",
            S3_SCRAPER_BUCKET,
            f"{CONFIGS['raw_urls_directory']}/group{i+1}{CONFIGS['output_urls_json_suffix']}",
        )


if __name__ == "__main__":
    lambda_handler(None, None)
