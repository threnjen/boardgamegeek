import gc
import os
from collections import defaultdict
from typing import Tuple

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
USER_CONFIGS = CONFIGS["users"]
RATINGS_CONFIGS = CONFIGS["ratings"]
IS_LOCAL = True if os.environ.get("IS_LOCAL", "False").lower() == "true" else False


class DirtyDataExtractor:

    def __init__(self) -> None:
        pass

    def data_extraction_chain(self):
        """Main function to extract data from the XML files"""
        file_list_to_process = self._get_file_list()
        all_ratings_with_dates = self._process_file_list_for_rating_dates(
            file_list_to_process
        )
        users_df = self._create_table_from_data(all_ratings_with_dates)
        self._save_dfs_to_disk_or_s3(
            directory="dirty_dfs_directory", table_name="user_data", df=users_df
        )
        merged_df = self.merge_with_other_ratings_file()
        self._save_dfs_to_disk_or_s3(
            directory="clean_dfs_directory",
            table_name="complete_user_ratings",
            df=merged_df,
        )

    def _get_file_list(self) -> list[str]:
        """Get the list of files to process"""

        xml_directory = USER_CONFIGS["output_xml_directory"]
        # file_list_to_process = []
        file_list_to_process = get_s3_keys_based_on_env(xml_directory)
        if not file_list_to_process:
            local_files = get_local_keys_based_on_env(xml_directory)
            file_list_to_process = [x for x in local_files if x.endswith(".xml")]
        print(f"\nUser files to process: {len(file_list_to_process)}")
        print(file_list_to_process[-5:])
        return file_list_to_process

    def _process_file_list_for_rating_dates(
        self, file_list_to_process: list
    ) -> list[dict]:
        """Process the list of files in the S3 bucket
        This function will process the list of files in the S3 bucket
        and extract the necessary information from the XML files. The
        function will return a list of dictionaries containing the data"""

        all_ratings_with_dates = []
        users_parsed = 0

        for file_name in file_list_to_process[:1]:

            local_open = load_file_local_first(
                path=USER_CONFIGS["output_xml_directory"],
                file_name=file_name.split("/")[-1],
            )

            game_page = BeautifulSoup(local_open, features="xml")

            username = file_name.split("user_")[-1].split(".xml")[0]
            # print(f"\nParsing user {username}")

            one_user_reviews = self._get_ratings_from_user(username, game_page)
            # print(f"Ratings for user {username}: {len(one_user_reviews)}")

            users_parsed += 1

            all_ratings_with_dates += one_user_reviews

            if users_parsed % 1000 == 0:
                print(f"\nTotal number of users processed: {users_parsed}")
                print(
                    f"Last user processed: {username} with {len(one_user_reviews)} ratings"
                )

        print(f"\nTotal number of ratings ratings processed: {users_parsed}")

        return all_ratings_with_dates

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

    def _create_table_from_data(
        self, all_ratings_with_dates: dict[list]
    ) -> pd.DataFrame:
        """Create a DataFrame from the data"""
        df = pd.DataFrame(
            all_ratings_with_dates,
            columns=["username", "BGGId", "rating", "lastmodified"],
        )
        df = df.sort_values(by="username").reset_index(drop=True)
        df = df.drop_duplicates()
        print(df.head())

        return df

    def merge_with_other_ratings_file(self):

        users_df = load_file_local_first(
            path=USER_CONFIGS["dirty_dfs_directory"], file_name=f"user_data.pkl"
        )
        ratings_df = load_file_local_first(
            path=RATINGS_CONFIGS["dirty_dfs_directory"], file_name=f"ratings_data.pkl"
        )
        print(ratings_df.info())
        print(users_df.info())

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
