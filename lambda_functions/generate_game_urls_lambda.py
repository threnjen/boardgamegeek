import pandas as pd
import json
import os
import awswrangler as wr
import math
import boto3

ENV = os.environ.get("ENV", "dev")
S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")
GAME_JSON_URLS_PREFIX = os.environ.get("GAME_JSON_URLS_PREFIX")
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

    local_path = "local_data/scraper_urls_raw_game" if ENV != "prod" else "/tmp"

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
        if ENV == "prod":
            s3_client = boto3.client("s3")
            s3_client.upload_file(
                f"{local_path}/group{i+1}_game_scraper_urls_raw.json",
                S3_SCRAPER_BUCKET,
                f"{GAME_JSON_URLS_PREFIX}/group{i+1}_game_scraper_urls_raw.json",
            )


if __name__ == "__main__":
    lambda_handler(None, None)
