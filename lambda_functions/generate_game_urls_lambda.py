import pandas as pd
import json
import os
import awswrangler as wr
import math

ENV = os.environ.get("ENV", "dev")
S3_BUCKET = os.environ.get("S3_BUCKET")

def generate_raw_urls(game_ids: list[str], block_size: int = 500):
    """Generate the raw urls for the scraper"""
    targets = [
        game_ids[i : i + block_size] for i in range(0, len(game_ids), block_size)
    ]

    return [
        f"https://www.boardgamegeek.com/xmlapi2/thing?id={','.join(block)}&stats=1&type=boardgame"
        for block in targets
    ]


def lambda_handler(event, context):

    # Get file from https://boardgamegeek.com/data_dumps/bg_ranks
    if ENV == "dev":
        df = pd.read_csv("data_store/local_files/boardgames_ranks.csv", low_memory=False)
    else:
        # read the file from S3
        df = wr.s3.read_csv(f"s3://{S3_BUCKET}/boardgames_ranks.csv")

    game_ids = df["id"].astype(str).to_list()
    block_size = 500

    scraper_urls_raw = generate_raw_urls(game_ids, block_size)

    print(len(scraper_urls_raw))
    block_size = math.ceil(len(scraper_urls_raw) / 10)
    print(block_size)

    # divide the list of scraper_raw_urls into 10 parts
    # and save them in separate files
    if ENV == "dev":
        for i in range(10):
            print(f"Saving block size {i * block_size} : {(i + 1) * block_size}")
            with open(f"data_store/local_files/scraper_urls_raw/scraper_urls_raw_{i}.json", "w") as convert_file:
                convert_file.write(json.dumps(scraper_urls_raw[i * block_size : (i + 1) * block_size]))
    else:
        # save the files to S3
        for i in range(10):
            wr.s3.to_json(
                df=pd.DataFrame(scraper_urls_raw[i * block_size : (i + 1) * block_size]),
                path=f"s3://{S3_BUCKET}/scraper_urls_raw/scraper_urls_raw_{i}.json",
            )

if __name__ == "__main__":
    lambda_handler(None, None)