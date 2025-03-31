import math
import os
import numpy as np
import pandas as pd
import sys
from abc import ABC
from datetime import datetime

from config import CONFIGS
from utils.processing_functions import load_file_local_first, save_file_local_first

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")
GAME_CONFIGS = CONFIGS["games"]
RATING_CONFIGS = CONFIGS["ratings"]
USER_CONFIGS = CONFIGS["users"]
URL_BLOCK_SIZE = 20
NUMBER_PROCESSES = 29


class UrlGenerator(ABC):

    def __init__(self):
        pass

    def _generate_urls_list(self) -> list[str]:
        return []

    def produce_urls(self):
        pass


class GameUrls(UrlGenerator):

    def _generate_urls_list(self, game_ids: list[str]):
        """Generate the raw urls for the scraper"""
        targets = [
            game_ids[i : i + URL_BLOCK_SIZE]
            for i in range(0, len(game_ids), URL_BLOCK_SIZE)
        ]
        print(f"Generated {len(targets)} URLS with block size {URL_BLOCK_SIZE}")

        return [
            f"https://www.boardgamegeek.com/xmlapi2/thing?id={','.join(block)}&stats=1&type=boardgame"
            for block in targets
        ]

    def produce_urls(self):
        df = load_file_local_first(file_name=CONFIGS["boardgamegeek_csv_filename"])

        game_ids = df["id"].astype(str).to_list()
        print(f"Number of game ids: {len(game_ids)}")

        scraper_urls_raw = self._generate_urls_list(game_ids)

        print(f"Number of scraper urls: {len(scraper_urls_raw)}")
        URL_BLOCK_SIZE = (
            math.ceil(len(scraper_urls_raw) / NUMBER_PROCESSES)
            if ENVIRONMENT == "prod"
            else 3
        )
        print(f"URL block size: {URL_BLOCK_SIZE}")

        for i in range(NUMBER_PROCESSES):
            print(
                f"Saving block size {i * URL_BLOCK_SIZE} : {(i + 1) * URL_BLOCK_SIZE}"
            )

            scraper_urls_set = scraper_urls_raw[
                i * URL_BLOCK_SIZE : (i + 1) * URL_BLOCK_SIZE
            ]

            save_file_local_first(
                path=f"{GAME_CONFIGS['raw_urls_directory']}",
                file_name=f"group{i+1}{GAME_CONFIGS['output_urls_json_suffix']}",
                data=scraper_urls_set,
            )

            if ENVIRONMENT != "prod":
                break


class RatingsUrls(UrlGenerator):

    def _generate_urls_list(self, game_entries):
        """Generate the raw urls for the scraper"""
        urls_list = []
        bgg_ids = game_entries[0]
        ratings_pages = game_entries[1]

        for i in list(range(0, len(bgg_ids))):
            current_bgg_id = bgg_ids[i]
            max_page_number = ratings_pages[i]
            page_numbers = range(1, max_page_number + 1)

            for page_number in page_numbers:
                path = f"https://www.boardgamegeek.com/xmlapi2/thing?id={current_bgg_id}&ratingcomments=1&page={str(page_number)}&pagesize=100"
                urls_list.append(path)

        return urls_list

    def produce_urls(self):
        """Generate the raw URLs for the ratings scraper
        This function will read the game ids from the local csv file or S3
        and generate the raw URLs for the ratings scraper. The URLs
        will be split into blocks and saved to S3 for the scraper
        to pick up."""

        games = load_file_local_first(
            path=f'{CONFIGS["games"]["dirty_dfs_directory"]}',
            file_name=GAME_CONFIGS["dirty_games_file"],
        )

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

        ratings_totals = ratings_totals.to_dict(orient="records")

        file_groups = {}
        group_counter = 1

        print(ratings_totals)

        print(
            f"Splitting the games into groups of ~{max_ratings_pages} ratings pages\n"
        )
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

            file_groups[f"group{group_counter}"] = [bgg_id_lists, ratings_lists]
            print(
                f"group{group_counter} Complete - {len(bgg_id_lists)} games with {chunk_size} ratings pages"
            )
            group_counter += 1

        group_urls = {}

        total_games_processed = 0
        total_pages_processed = 0

        print(f"\nWriting the urls to json files\n")

        for group, game_entries in file_groups.items():

            print(f"{len(game_entries[0])} games in {group}")
            group_urls = self._generate_urls_list(game_entries)

            if ENVIRONMENT != "prod":
                group_urls = group_urls[:3]

            save_file_local_first(
                path=RATING_CONFIGS["raw_urls_directory"],
                file_name=f"{group}{RATING_CONFIGS['output_urls_json_suffix']}",
                data=group_urls,
            )

            total_games_processed += len(game_entries[0])
            total_pages_processed += sum(game_entries[1])

            if ENVIRONMENT != "prod":
                break

        print(f"\nTotal games processed: {total_games_processed}")
        print(f"Total pages processed: {total_pages_processed}")


class UserUrls(UrlGenerator):

    def _generate_urls_list(self, user_ids):
        """Generate the raw urls for the scraper"""

        urls_list = []

        for user_id in user_ids:
            path = f"https://boardgamegeek.com/xmlapi2/collection?username={user_id}&rated=1&stats=1"
            urls_list.append(path)

        return urls_list

    def produce_urls(self):
        """Generate the raw URLs for the ratings scraper
        This function will read the game ids from the local csv file or S3
        and generate the raw URLs for the ratings scraper. The URLs
        will be split into blocks and saved to S3 for the scraper
        to pick up."""

        timestamp = datetime.now().strftime("%Y%m%d")
        users = load_file_local_first(
            path=f"ratings",
            file_name=f"unique_ids_{timestamp}.json",
        )

        user_ids = list(users.values())[0]
        print(type(user_ids))
        print(f"\nNumber of user ids: {len(user_ids)}\n")

        total_url_files = 29
        total_users = len(user_ids)
        urls_per_file = total_users // total_url_files

        print(f"urls per file {urls_per_file}")

        # generate blocks of urls
        url_blocks = {}

        total_users_processed = 0
        block = 0

        for i in range(0, total_url_files):
            group_num = i + 1
            url_blocks[group_num] = user_ids[block : block + urls_per_file]

            print(f"{len(url_blocks[group_num])} users in group{group_num}")
            group_urls = self._generate_urls_list(url_blocks[group_num])

            if ENVIRONMENT != "prod":
                group_urls = group_urls[:20]

            save_file_local_first(
                path=USER_CONFIGS["raw_urls_directory"],
                file_name=f"group{group_num}{USER_CONFIGS['output_urls_json_suffix']}",
                data=group_urls,
            )

            total_users_processed += len(url_blocks[group_num])

            block += urls_per_file

            if ENVIRONMENT != "prod":
                break

        print(f"\nTotal users processed: {total_users_processed}")


def lambda_handler(event, context):
    class_reference = {
        "games": GameUrls,
        "ratings": RatingsUrls,
        "users": UserUrls,
    }
    class_reference.get(event["data_type"])().produce_urls()


if __name__ == "__main__":
    data_type = sys.argv[1]

    lambda_handler({"data_type": data_type}, None)
