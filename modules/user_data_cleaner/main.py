import gc
import os
from collections import defaultdict

import pandas as pd
from bs4 import BeautifulSoup

from config import CONFIGS
from utils.processing_functions import (
    get_local_keys_based_on_env,
    get_s3_keys_based_on_env,
    load_file_local_first,
    save_file_local_first,
    save_to_aws_glue,
)

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
S3_SCRAPER_BUCKET = CONFIGS["s3_scraper_bucket"]
USER_CONFIGS = CONFIGS["user"]
IS_LOCAL = True if os.environ.get("IS_LOCAL", "False").lower() == "true" else False


class DirtyDataExtractor:

    def __init__(self) -> None:
        self.total_entries = 0

    def data_extraction_chain(self):
        file_list_to_process = self._get_file_list()
        all_entries = self._process_file_list(file_list_to_process)
        raw_storage = self._organize_raw_data(all_entries)
        self._validate_dictionary_creation(raw_storage)
        self._create_table_from_data(raw_storage)
        # self._save_dfs_to_disk_or_s3(dirty_storage)

    def _get_file_list(self) -> list[str]:
        # list files in data dirty prefix in s3 using awswrangler
        xml_directory = USER_CONFIGS["output_xml_directory"]
        file_list_to_process = get_s3_keys_based_on_env(xml_directory)
        if not file_list_to_process:
            local_files = get_local_keys_based_on_env(xml_directory)
            file_list_to_process = [x for x in local_files if x.endswith(".xml")]
        return file_list_to_process

    def _process_file_list(self, file_list_to_process: list) -> list[dict]:
        """Process the list of files in the S3 bucket
        This function will process the list of files in the S3 bucket
        and extract the necessary information from the XML files. The
        function will return None."""

        all_entries = []

        for file in file_list_to_process:

            game_entries = self._get_beautiful_soup(file)

            for game_entry in game_entries:

                one_game_reviews_dict = self._get_ratings_from_game(game_entry)
                print(
                    f"Number of ratings ID {game_entry['id']}: {len(one_game_reviews_dict)}"
                )
                self.total_entries += len(one_game_reviews_dict)

                all_entries.append(one_game_reviews_dict)

        print(f"\nTotal number of user ratings processed: {self.total_entries}")

        return all_entries

    def _get_beautiful_soup(self, file) -> BeautifulSoup:
        local_open = load_file_local_first(
            path=USER_CONFIGS["output_xml_directory"],
            file_name=file.split("/")[-1],
        )

        game_page = BeautifulSoup(local_open, features="xml")

        game_entries = game_page.find_all("item")

        print(f"\nTotal number of game entries in file: {len(game_entries)}\n")

        return game_entries

    def _get_ratings_from_game(self, game_entry) -> dict:
        """Parse the individual game data"""
        game_id = game_entry["id"]
        comments = game_entry.find_all("comment")

        user_ratings = self._create_ratings_dict_by_user(game_id, comments)

        return user_ratings

    def _create_ratings_dict_by_user(self, game_id, comments: list) -> dict:
        """Create a dictionary of ratings by user"""
        user_ratings = {}

        for comment in comments:
            username = comment["username"]
            user_ratings[username] = []
            user_ratings[username].append(game_id)
            user_ratings[username].append(comment["rating"])
            user_ratings[username].append(comment["value"])

        return user_ratings

    def _organize_raw_data(self, all_entries: list[dict]) -> dict[list]:
        """Organize the raw data into a dictionary of lists"""
        raw_storage = defaultdict(list)

        for game_set in all_entries:
            for username, game_data in game_set.items():
                if not raw_storage.get(username):
                    raw_storage[username] = []
                raw_storage[username].append(game_data)

        return raw_storage

    def _validate_dictionary_creation(self, raw_storage: dict[list]) -> dict[list]:
        """Make a dictionary where the key is the username and the value is the length of the list of games"""
        user_game_count = {k: len(v) for k, v in raw_storage.items()}
        print(f"Number of unique users: {len(user_game_count)}")
        num_logged_ratings = sum(user_game_count.values())
        assert (
            num_logged_ratings == self.total_entries
        ), f"Number of ratings logged: {num_logged_ratings} != {self.total_entries}"
        return user_game_count

    def _create_table_from_data(self, raw_storage: dict[list]) -> dict[pd.DataFrame]:
        df = pd.DataFrame(raw_storage)
        print(df.head())

    def _organize_raw_storage(self, raw_storage: dict[list]) -> dict[pd.DataFrame]:
        print("Crafting data frames")

        dirty_storage = {}

        for table_name, list_of_entries in raw_storage.items():
            print(f"Len of {table_name}: {len(list_of_entries)}")

            if not list_of_entries:
                continue

            print(f"Creating table for {table_name}")
            if table_name != "games":
                combined_entries = defaultdict(list)
                for d in list_of_entries:
                    for key, value in d.items():
                        combined_entries[key].extend(value)
                list_of_entries = dict(combined_entries)
                table = pd.DataFrame.from_dict(list_of_entries)

            else:
                table = pd.DataFrame(list_of_entries)
                self._make_json_game_lookup_file(table)

            print(f"Deleting {table_name} from memory")
            del list_of_entries

            if None in table.columns:
                table = table.drop(columns=[None])
            else:
                pass

            table = table.sort_values(by="BGGId").reset_index(drop=True)

            dirty_storage[table_name] = table

        del raw_storage
        return dirty_storage

    def save_file_set(self, data, table):
        save_file_local_first(
            path=USER_CONFIGS["dirty_dfs_directory"],
            file_name=f"{table}_dirty.pkl",
            data=data,
        )
        save_file_local_first(
            path=USER_CONFIGS["dirty_dfs_directory"],
            file_name=f"{table}_dirty.csv",
            data=data,
        )
        save_to_aws_glue(data=data, table=f"{table}_dirty")

    def _save_dfs_to_disk_or_s3(self, dirty_storage: dict[pd.DataFrame]):
        """Save all files as pkl files. Save to local drive in ENVIRONMENT==env, or
        copy pkl to s3 if ENVIRONMENT==prod"""

        for table_name, table in dirty_storage.items():

            print(f"Saving {table_name} to disk and uploading to S3")

            print(table.dtypes)

            save_file_local_first(
                path=USER_CONFIGS["dirty_dfs_directory"],
                file_name=f"{table_name}.csv",
                data=table,
            )

            table = load_file_local_first(
                path=USER_CONFIGS["dirty_dfs_directory"], file_name=f"{table_name}.csv"
            )

            print(table.dtypes)

            self.save_file_set(data=table, table=table_name)

            del table
            gc.collect()


if __name__ == "__main__":

    DirtyDataExtractor().data_extraction_chain()
