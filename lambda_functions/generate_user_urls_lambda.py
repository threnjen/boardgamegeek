import pandas as pd
import json
import os
import awswrangler as wr
import numpy as np

ENV = os.environ.get("ENV", "dev")
S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")
url_block_size = 20
number_url_files = 30
NUMBER_PROCESSES = 50


def generate_ratings_urls(game_entries):
    urls_list = []
    bgg_ids = game_entries[0]
    ratings_pages = game_entries[1]

    for i in list(range(0, len(bgg_ids))):
        current_bgg_id = bgg_ids[i]
        max_page_number = ratings_pages[i]
        page_numbers = range(1, max_page_number + 1)
        print(f"{current_bgg_id} - {max_page_number} pages")

        for page_number in page_numbers:
            path = f"https://www.boardgamegeek.com/xmlapi2/thing?id={current_bgg_id}&ratingcomments=1&page={str(page_number)}&pagesize=100"
            urls_list.append(path)
    print("\n")

    return urls_list


def lambda_handler(event, context):

    # Get this file manually from https://boardgamegeek.com/data_dumps/bg_ranks
    if ENV == "dev":
        print("Reading the file locally")
        games = pd.read_pickle("../game_data_cleaner/game_dfs_dirty/games.pkl")
    else:
        print("Reading the file from S3")
        # download the pickle file from S3
        wr.s3.download(
            path=f"s3://{S3_SCRAPER_BUCKET}/game_dfs_dirty/games.pkl",
            local_file="games.pkl",
        )
        games = pd.read_pickle("games.pkl")

    ratings_totals = pd.DataFrame(games["BGGId"])
    ratings_totals["RatingsPages"] = np.ceil(games["NumUserRatings"].astype(int) / 100).astype("int")
    ratings_totals = ratings_totals.sort_values(
        "RatingsPages", ascending=False
    ).reset_index(drop=True)

    total_ratings = ratings_totals["RatingsPages"].sum()
    max_ratings_pages = int(np.ceil(total_ratings/NUMBER_PROCESSES))
    max_ratings_pages

    df_groups = {}
    group_counter = 1
    position = 0

    while len(ratings_totals) > 0:

        chunk_size = 0
        bgg_id_lists = []
        ratings_lists = []

        while max_ratings_pages > chunk_size:
            try:
                num_ratings = ratings_totals.iloc[position]['RatingsPages']
                bgg_id = ratings_totals.iloc[position]['BGGId']
                bgg_id_lists.append(bgg_id)
                ratings_lists.append(num_ratings)
                chunk_size += num_ratings
                ratings_totals = ratings_totals.drop(position)
                position += 1

            except:
                break

        # print(chunk_size)
        if len(bgg_id_lists) == 0:
            break
        df_groups[f"group{group_counter}"] = [bgg_id_lists, ratings_lists]
        # print(f"group{group_counter} Complete - {len(bgg_id_lists)} games with {chunk_size} ratings")
        group_counter += 1
    
    group_urls = {}

    for group, game_entries in df_groups.items():
        group_urls = generate_ratings_urls(game_entries)

        with open(f"../game_user_scraper/scraper_urls_raw/{group}_scraper_urls_ratings.json", "w") as convert_file:
            convert_file.write(json.dumps(group_urls))


if __name__ == "__main__":
    lambda_handler(None, None)
