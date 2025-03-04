import os

from datetime import datetime

import pandas as pd
from bs4 import BeautifulSoup

from config import CONFIGS
from utils.processing_functions import (
    get_xml_file_keys_based_on_env,
    load_file_local_first,
    save_file_local_first,
    save_dfs_to_disk_or_s3,
)
from utils.nlp_functions import filter_stopwords, evaluate_quality_words_over_thresh

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
S3_SCRAPER_BUCKET = CONFIGS["s3_scraper_bucket"]
RATING_CONFIGS = CONFIGS["ratings"]
IS_LOCAL = True if os.environ.get("IS_LOCAL", "False").lower() == "true" else False


class DirtyDataExtractor:

    def __init__(self) -> None:
        self.total_entries = 0

    def data_extraction_chain(self):
        """Main function to extract data from the XML files"""
        file_list_to_process = get_xml_file_keys_based_on_env(
            xml_directory=RATING_CONFIGS["output_xml_directory"]
        )
        all_entries = self._process_file_list(file_list_to_process)
        ratings_df = self._create_table_from_data(all_entries)
        save_dfs_to_disk_or_s3(
            df=ratings_df,
            table_name="ratings_data",
            path=RATING_CONFIGS["dirty_dfs_directory"],
        )
        quality_df = self._create_quality_review_table(ratings_df)
        save_dfs_to_disk_or_s3(
            df=quality_df,
            table_name="quality_ratings",
            path=RATING_CONFIGS["clean_dfs_directory"],
        )
        self._create_file_of_unique_user_ids(ratings_df)

    def _process_file_list(self, file_list_to_process: list) -> list[dict]:
        """Process the list of files in the S3 bucket
        This function will process the list of files in the S3 bucket
        and extract the necessary information from the XML files. The
        function will return a list of dictionaries containing the data"""

        all_entries = []

        for file in file_list_to_process:

            game_entries = self._get_beautiful_soup(file_name=file)

            for game_entry in game_entries:

                one_game_reviews = self._get_ratings_from_game(game_entry)

                self.total_entries += len(one_game_reviews)

                all_entries += one_game_reviews

        print(f"\nTotal number of ratings ratings processed: {self.total_entries}")

        return all_entries

    def _get_beautiful_soup(self, file_name: str) -> list[BeautifulSoup]:
        """Get the BeautifulSoup object for the XML file"""
        local_open = load_file_local_first(
            path=RATING_CONFIGS["output_xml_directory"],
            file_name=file_name.split("/")[-1],
        )

        game_page = BeautifulSoup(local_open, features="xml")

        game_entries = game_page.find_all("item")

        print(f"\nTotal number of game entries in file: {len(game_entries)}\n")

        return game_entries

    def _get_ratings_from_game(self, game_entry: BeautifulSoup) -> list[list]:
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
        df = df.sort_values(by="username").reset_index(drop=True)
        df = df.drop_duplicates()
        print(df.head())

        return df

    def _create_quality_review_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create a cleaned and refined table of data"""
        df = df[df["value"].notna()]

        df["value"] = df["value"].replace(r"[^A-Za-z0-9 ]+", "", regex=True)
        df["value"] = df["value"].str.lower().apply(lambda x: filter_stopwords(x))
        df["value"] = df["value"].str.replace("  ", " ")

        df["quality_review"] = df["value"].apply(evaluate_quality_words_over_thresh)
        df = df[df["quality_review"] == True]

        df = df.drop(columns=["quality_review"])
        return df

    def _create_file_of_unique_user_ids(self, ratings_df: pd.DataFrame) -> list:
        """Create a list of unique user IDs"""

        if ENVIRONMENT == "prod":
            user_ratings_count_df = ratings_df.groupby("username").count()["rating"]
            ratings_names_less_than_5 = user_ratings_count_df[
                user_ratings_count_df < 5
            ].index
            ratings_df = ratings_df.drop(
                ratings_df[ratings_df["username"].isin(ratings_names_less_than_5)].index
            )

        ratings_df["username"] = ratings_df["username"].astype(str)
        unique_ids = {"list_of_ids": sorted(ratings_df["username"].unique().tolist())}

        timestamp = datetime.now().strftime("%Y%m%d")
        save_file_local_first(
            path="ratings", file_name=f"unique_ids_{timestamp}.json", data=unique_ids
        )


if __name__ == "__main__":

    DirtyDataExtractor().data_extraction_chain()
