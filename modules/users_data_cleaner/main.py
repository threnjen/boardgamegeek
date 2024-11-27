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
from typing import Tuple

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
S3_SCRAPER_BUCKET = CONFIGS["s3_scraper_bucket"]
USER_CONFIGS = CONFIGS["users"]
RATINGS_CONFIGS = CONFIGS["ratings"]
IS_LOCAL = True if os.environ.get("IS_LOCAL", "False").lower() == "true" else False


class DirtyDataExtractor:

    def __init__(self) -> None:
        self.total_entries = 0

    def data_extraction_chain(self):
        """Main function to extract data from the XML files"""
        file_list_to_process = self._get_file_list()
        all_entries = self._process_file_list(file_list_to_process)
        users_df = self._create_table_from_data(all_entries)
        self._save_dfs_to_disk_or_s3(
            directory="dirty_dfs_directory", table_name="user_data", df=users_df
        )
        merged_df = self.merge_with_other_ratings_file(users_df)
        self._save_dfs_to_disk_or_s3(
            directory="clean_dfs_directory",
            table_name="complete_user_ratings",
            df=merged_df,
        )

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

            user_entries = self._get_individual_user(file_name=file)

            for user_entry in user_entries:

                user_entry = BeautifulSoup(str(user_entry), features="xml")
                username = user_entry.find("username").get("value")
                print(f"\nParsing user {username}")

                one_user_reviews = self._get_ratings_from_user(username, user_entry)
                print(f"Ratings for user {username}: {len(one_user_reviews)}")

                self.total_entries += len(one_user_reviews)

                all_entries += one_user_reviews

        print(f"\nTotal number of ratings ratings processed: {self.total_entries}")

        return all_entries

    def _get_individual_user(self, file_name: str) -> Tuple[str, list[BeautifulSoup]]:
        """Get the BeautifulSoup object for the XML file"""
        local_open = load_file_local_first(
            path=USER_CONFIGS["output_xml_directory"],
            file_name=file_name.split("/")[-1],
        )

        game_page = BeautifulSoup(local_open, features="xml")

        user_entries = game_page.find_all("username")

        print(f"\nTotal number of users in file: {len(user_entries)}\n")

        return user_entries

    def _get_ratings_from_user(
        self, username: str, user_entry: BeautifulSoup
    ) -> list[list]:
        """Parse the individual game data"""

        user_ratings = []

        all_ratings = user_entry.find_all("item")
        for individual_rating in all_ratings:
            soupified_xml = BeautifulSoup(str(individual_rating), features="xml")
            game_id = soupified_xml.find("item").get("objectid")
            rating = soupified_xml.find("rating").get("value")
            lastmodified = soupified_xml.find("status").get("lastmodified")
            user_ratings.append([username, game_id, rating, lastmodified])

        return user_ratings

    def _create_table_from_data(self, all_entries: dict[list]) -> pd.DataFrame:
        """Create a DataFrame from the data"""
        df = pd.DataFrame(
            all_entries, columns=["username", "BGGId", "rating", "lastmodified"]
        )
        df = df.sort_values(by="username").reset_index(drop=True)
        df = df.drop_duplicates()
        print(df.head())

        return df

    def merge_with_other_ratings_file(self, users_df):
        ratings_df = load_file_local_first(
            path=RATINGS_CONFIGS["clean_dfs_directory"], file_name=f"ratings_data.pkl"
        )

        merged_df = pd.merge(
            ratings_df[["username", "BGGId", "rating", "value"]],
            users_df[["username", "BGGId", "lastmodified"]],
            on=["username", "BGGId"],
            how="inner",
        )

        return merged_df

    def _save_dfs_to_disk_or_s3(self, directory, table_name, df: dict[pd.DataFrame]):
        """Save all files as pkl files and csv files"""

        print(f"\nSaving ratings data to disk and uploading to S3")

        # save and load as csv to properly infer data types
        save_file_local_first(
            path=USER_CONFIGS[directory],
            file_name=f"{table_name}.csv",
            data=df,
        )

        df = load_file_local_first(
            path=USER_CONFIGS[directory], file_name=f"{table_name}.csv"
        )

        # save completed dataframes
        save_file_local_first(
            path=USER_CONFIGS[directory],
            file_name=f"{table_name}.pkl",
            data=df,
        )
        save_file_local_first(
            path=USER_CONFIGS[directory],
            file_name=f"{table_name}.csv",
            data=df,
        )
        if ENVIRONMENT == "prod":
            save_to_aws_glue(data=df, table=f"{table_name}")


if __name__ == "__main__":

    DirtyDataExtractor().data_extraction_chain()
