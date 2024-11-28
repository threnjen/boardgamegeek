import math
import os

from config import CONFIGS
from utils.processing_functions import load_file_local_first, save_file_local_first

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")
GAME_CONFIGS = CONFIGS["games"]

url_block_size = 20
number_url_files = 29


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

    df = load_file_local_first(file_name="boardgames_ranks.csv")

    game_ids = df["id"].astype(str).to_list()
    print(f"Number of game ids: {len(game_ids)}")

    scraper_urls_raw = generate_raw_urls(game_ids)

    print(f"Number of scraper urls: {len(scraper_urls_raw)}")
    url_block_size = (
        math.ceil(len(scraper_urls_raw) / number_url_files)
        if ENVIRONMENT == "prod"
        else 3
    )
    print(f"URL block size: {url_block_size}")

    for i in range(number_url_files):
        print(f"Saving block size {i * url_block_size} : {(i + 1) * url_block_size}")

        scraper_urls_set = scraper_urls_raw[
            i * url_block_size : (i + 1) * url_block_size
        ]

        save_file_local_first(
            path=f"{GAME_CONFIGS['raw_urls_directory']}",
            file_name=f"group{i+1}{GAME_CONFIGS['output_urls_json_suffix']}",
            data=scraper_urls_set,
        )

        if ENVIRONMENT != "prod":
            break


if __name__ == "__main__":
    lambda_handler(None, None)
