import json
import os

import awswrangler as wr
import boto3
import numpy as np
import pandas as pd

from config import CONFIGS

ENV = os.environ.get("ENV", "dev")
S3_SCRAPER_BUCKET = CONFIGS["s3_scraper_bucket"]
url_block_size = 20
number_url_files = 30
NUMBER_PROCESSES = 30


def generate_ratings_urls(game_entries):
    """Generate the raw urls for the scraper"""
    urls_list = []
    bgg_ids = game_entries[0]
    ratings_pages = game_entries[1]

    for i in list(range(0, len(bgg_ids))):
        current_bgg_id = bgg_ids[i]
        max_page_number = ratings_pages[i]
        page_numbers = range(1, max_page_number + 1)
        # print(f"{current_bgg_id} - {max_page_number} pages")

        for page_number in page_numbers:
            path = f"https://www.boardgamegeek.com/xmlapi2/thing?id={current_bgg_id}&ratingcomments=1&page={str(page_number)}&pagesize=100"
            urls_list.append(path)

    return urls_list


def lambda_handler(event, context):
    """Generate the raw URLs for the user scraper
    This function will read the game ids from the local csv file or S3
    and generate the raw URLs for the user scraper. The URLs
    will be split into blocks and saved to S3 for the scraper
    to pick up."""

    # Get this file manually from https://boardgamegeek.com/data_dumps/bg_ranks
    try:
        games = pd.read_pickle(f'{CONFIGS["game"]["dirty_dfs_directory"]}/games.pkl')
        print("Reading the games.pkl file locally")

    except:
        print("Reading the games.pkl file from S3")
        # download the pickle file from S3
        wr.s3.download(
            path=f"s3://{S3_SCRAPER_BUCKET}/game_dfs_dirty/games.pkl",
            local_file="games.pkl",
        )
        games = pd.read_pickle("games.pkl")

    ratings_totals = pd.DataFrame(games["BGGId"])

    game_ids = ratings_totals["BGGId"].astype(str).to_list()
    print(f"\nNumber of game ids: {len(game_ids)}\n")

    ratings_totals["RatingsPages"] = np.ceil(
        games["NumUserRatings"].astype(int) / 100
    ).astype("int")

    total_ratings = ratings_totals["RatingsPages"].sum()
    print(f"Total pages of ratings: {total_ratings}\n")

    print(
        f"Number of games with no ratings: {len(ratings_totals[ratings_totals['RatingsPages'] == 0])}\n"
    )

    ratings_totals = ratings_totals.sort_values(
        "RatingsPages", ascending=False
    ).reset_index(drop=True)

    max_ratings_pages = int(np.ceil(total_ratings / NUMBER_PROCESSES))
    print(
        f"Max ratings pages per process to spawn {NUMBER_PROCESSES} processes: {max_ratings_pages}\n"
    )

    # turn ratings total into a dictionary
    ratings_totals = ratings_totals.to_dict(orient="records")
    print(ratings_totals)

    # END SETUP METRICS

    df_groups = {}
    group_counter = 1

    print(f"Splitting the games into groups of ~{max_ratings_pages} ratings pages\n")
    while len(ratings_totals) > 0:

        chunk_size = 0
        bgg_id_lists = []
        ratings_lists = []

        while max_ratings_pages > chunk_size:

            num_ratings = ratings_totals[0]["RatingsPages"]
            bgg_id = ratings_totals[0]["BGGId"]
            bgg_id_lists.append(bgg_id)
            ratings_lists.append(num_ratings)
            chunk_size += num_ratings
            del ratings_totals[0]
            if len(ratings_totals) == 0:
                break

        df_groups[f"group{group_counter}"] = [bgg_id_lists, ratings_lists]
        print(
            f"group{group_counter} Complete - {len(bgg_id_lists)} games with {chunk_size} ratings pages"
        )
        group_counter += 1

    group_urls = {}

    raw_urls_directory = CONFIGS["user"]["raw_urls_directory"]
    local_path = "/tmp" if ENV == "prod" else f"data/{raw_urls_directory}"

    total_games_processed = 0
    total_pages_processed = 0

    print(f"\nWriting the urls to json files\n")

    for group, game_entries in df_groups.items():

        print(f"{len(game_entries[0])} games in {group}")
        group_urls = generate_ratings_urls(game_entries)

        output_urls_json_suffix = CONFIGS["user"]["output_urls_json_suffix"]

        with open(
            f"{local_path}/{group}{output_urls_json_suffix}",
            "w",
        ) as convert_file:
            convert_file.write(json.dumps(group_urls))

        if ENV == "prod":
            # upload the json to S3 with boto3
            s3_client = boto3.client("s3")
            s3_client.upload_file(
                f"{local_path}/{group}{output_urls_json_suffix}",
                S3_SCRAPER_BUCKET,
                f"{raw_urls_directory}/{group}{output_urls_json_suffix}",
            )

        total_games_processed += len(game_entries[0])
        total_pages_processed += sum(game_entries[1])

    print(f"\nTotal games processed: {total_games_processed}")
    print(f"Total pages processed: {total_pages_processed}")


if __name__ == "__main__":
    lambda_handler(None, None)
