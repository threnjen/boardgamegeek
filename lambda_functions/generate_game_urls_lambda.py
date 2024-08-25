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

    # Get this file manually from https://boardgamegeek.com/data_dumps/bg_ranks
    if ENV == "dev":
        print("Reading the file locally")
        df = pd.read_csv(
            "data_store/local_files/boardgames_ranks.csv", low_memory=False
        )
    else:
        print("Reading the file from S3")
        # read the file from S3
        df = wr.s3.read_csv(f"s3://{S3_SCRAPER_BUCKET}/boardgames_ranks.csv")

    game_ids = df["id"].astype(str).to_list()
    print(f"Number of game ids: {len(game_ids)}")

    scraper_urls_raw = generate_raw_urls(game_ids)

    print(len(scraper_urls_raw))
    url_block_size = math.ceil(len(scraper_urls_raw) / number_url_files)
    print(f"URL block size: {url_block_size}")

    # divide the list of scraper_raw_urls into number_url_files parts
    # and save them in separate files

    local_path = "data_store/local_files/scraper_urls_raw" if ENV != "prod" else "/tmp"

    for i in range(number_url_files):
        print(f"Saving block size {i * url_block_size} : {(i + 1) * url_block_size}")
        with open(f"{local_path}/scraper_urls_raw_{i}.json", "w") as convert_file:
            convert_file.write(
                json.dumps(
                    scraper_urls_raw[i * url_block_size : (i + 1) * url_block_size]
                )
            )
        if ENV == "prod":
            # upload the json to S3 with boto3
            s3_client = boto3.client("s3")
            s3_client.upload_file(
                f"{local_path}/scraper_urls_raw_{i}.json",
                S3_SCRAPER_BUCKET,
                f"{GAME_JSON_URLS_PREFIX}/scraper_urls_raw_{i}.json",
            )


if __name__ == "__main__":
    lambda_handler(None, None)
