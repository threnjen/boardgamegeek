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
        """Main function to extract data from the XML files"""
        file_list_to_process = self._get_file_list()
        all_entries = self._process_file_list(file_list_to_process)
        user_df = self._create_table_from_data(all_entries)
        self._save_dfs_to_disk_or_s3(user_df)

    def _get_file_list(self) -> list[str]:
        """Get the list of files to process"""

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
        function will return a list of dictionaries containing the data"""

        all_entries = []

        for file in file_list_to_process:

            game_entries = self._get_beautiful_soup(file)

            for game_entry in game_entries:

                one_game_reviews = self._get_ratings_from_game(game_entry)
                print(
                    f"Number of ratings ID {game_entry['id']}: {len(one_game_reviews)}"
                )
                self.total_entries += len(one_game_reviews)

                all_entries += one_game_reviews

        print(f"\nTotal number of user ratings processed: {self.total_entries}")

        return all_entries

    def _get_beautiful_soup(self, file) -> BeautifulSoup:
        """Get the BeautifulSoup object for the XML file"""
        local_open = load_file_local_first(
            path=USER_CONFIGS["output_xml_directory"],
            file_name=file.split("/")[-1],
        )

        game_page = BeautifulSoup(local_open, features="xml")

        game_entries = game_page.find_all("item")

        print(f"\nTotal number of game entries in file: {len(game_entries)}\n")

        return game_entries

    def _get_ratings_from_game(self, game_entry) -> list:
        """Parse the individual game data"""
        game_id = game_entry["id"]
        comments = game_entry.find_all("comment")

        user_ratings = []

        for comment in comments:
            user_ratings.append(
                [comment["username"], game_id, comment["rating"], comment["value"]]
            )

        return user_ratings

    def _create_table_from_data(self, all_entries: dict[list]) -> pd.DataFrame:
        """Create a DataFrame from the data"""
        df = pd.DataFrame(all_entries, columns=["username", "BGGId", "rating", "value"])
        df = df.sort_values(by="username").reset_index(drop=True).set_index("username")
        print(df.head())

        return df

    def _save_dfs_to_disk_or_s3(self, user_df: dict[pd.DataFrame]):
        """Save all files as pkl files and csv files"""

        print(f"\nSaving user data to disk and uploading to S3")

        table_name = "user_data"

        # save and load as csv to properly infer data types
        save_file_local_first(
            path=USER_CONFIGS["clean_dfs_directory"],
            file_name=f"{table_name}.csv",
            data=user_df,
        )

        user_df = load_file_local_first(
            path=USER_CONFIGS["clean_dfs_directory"], file_name=f"{table_name}.csv"
        )

        save_file_local_first(
            path=USER_CONFIGS["clean_dfs_directory"],
            file_name=f"{table_name}.pkl",
            data=user_df,
        )
        save_file_local_first(
            path=USER_CONFIGS["clean_dfs_directory"],
            file_name=f"{table_name}.csv",
            data=user_df,
        )
        if ENVIRONMENT == "prod":
            save_to_aws_glue(data=user_df, table=f"{table_name}")


if __name__ == "__main__":

    DirtyDataExtractor().data_extraction_chain()