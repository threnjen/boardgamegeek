import pandas as pd
import numpy as np
import requests
import re
import time
import os
import gc
import json
from datetime import datetime

# from statistics import mean
# NLP tools
# import spacy

# nlp = spacy.load("en_core_web_sm")
# import re
# import nltk
# from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
# from nltk.tokenize import word_tokenize

from utils.s3_file_handler import S3FileHandler
from utils.local_file_handler import LocalFileHandler
from utils.processing_functions import (
    integer_reduce,
    save_file_local_first,
    load_file_local_first,
)
from config import CONFIGS

GAME_CONFIGS = CONFIGS["game"]
ENV = os.getenv("ENV", "dev")


class GameDataCleaner:

    def __init__(self) -> None:
        self.s3_file_handler = S3FileHandler()
        self.local_handler = LocalFileHandler()
        self.game_mappings = LocalFileHandler().load_file(
            file_path="game_data_cleaner/game_mappings.json"
        )

    def cleaning_chain(self) -> pd.DataFrame:

        print("\nCleaning Games Data")
        games_df = load_file_local_first(
            path=GAME_CONFIGS["dirty_dfs_directory"], file_name="games.pkl"
        )
        games_df = self._drop_duplicates(games_df)
        games_df = self._drop_unneeded_columns(games_df)
        games_df = self._clean_best_players(games_df)
        games_df = self._add_binary_category_flags(games_df)
        games_df = self._reduce_integers_for_memory_usage(games_df)
        games_df = self._drop_unreleased(games_df)
        games_df = self._set_missing_min_players(games_df)
        themes_df = self._breakout_themes_df(games_df)
        games_df = self._drop_themes(games_df)
        save_file_local_first(
            path=GAME_CONFIGS["game_dfs_clean"], file_name="games.pkl", data=games_df
        )
        save_file_local_first(
            path=GAME_CONFIGS["dirty_dfs_directory"],
            file_name="themes.pkl",
            data=themes_df,
        )
        print("Finishes Cleaning Games Data\n")

    def load_games_data(self, file_path: str) -> pd.DataFrame:
        """Load games data from a file path"""
        games_df = self.local_handler.load_file(file_path)
        return games_df

    def _drop_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.drop_duplicates(subset="BGGId", keep="first")
        return df

    def _drop_unneeded_columns(self, df: pd.DataFrame) -> pd.DataFrame:

        drop_columns = self.game_mappings["drop_columns"]

        # drop non-boardgame related information
        for column in drop_columns:
            if column in df.columns:
                df = df.drop(column, axis=1)

        return df

    def _clean_best_players(self, df: pd.DataFrame) -> pd.DataFrame:

        # Get rid of all non-integer characters from df["BestPlayers"] using regex
        df["BestPlayers"] = df["BestPlayers"].str.replace(r"\D", "", regex=True)

        # change the datatype of BestPlayers to int8
        df["BestPlayers"] = pd.to_numeric(
            df["BestPlayers"], errors="coerce", downcast="integer"
        )

        # fill in missing values with 0
        df["BestPlayers"] = df["BestPlayers"].fillna(0)

        df["BestPlayers"] = df["BestPlayers"].astype("int8")

        return df

    def _add_binary_category_flags(self, df: pd.DataFrame) -> pd.DataFrame:

        for field, category in self.game_mappings["binary_flag_fields"].items():
            if field in df.columns:
                df.loc[df[field].notna(), category] = 1

        print(df.head())

        return df

    def _reduce_integers_for_memory_usage(self, df: pd.DataFrame) -> pd.DataFrame:

        int_columns = [x for x in self.game_mappings["int_columns"] if x in df.columns]
        rank_columns = [
            x for x in self.game_mappings["rank_columns"] if x in df.columns
        ]

        df = integer_reduce(df, int_columns, fill_value=0)

        df = integer_reduce(df, rank_columns, fill_value=df.shape[0] + 1)

        return df

    def _drop_unreleased(self, df: pd.DataFrame) -> pd.DataFrame:

        # get this year from datetime
        next_year = datetime.now().year + 1

        df = df[df["YearPublished"] < next_year]
        return df

    def _set_missing_min_players(self, df: pd.DataFrame) -> pd.DataFrame:
        df["MinPlayers"] = df["MinPlayers"].fillna(2)
        df.loc[df["MinPlayers"] == 0, "MinPlayers"] = 2
        return df

    def _breakout_themes_df(self, df: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame(df[["BGGId", "Theme"]]).copy()

    def _drop_themes(self, df: pd.DataFrame):
        return df.drop("Theme", axis=1)


if __name__ == "__main__":
    cleaner = GameDataCleaner().cleaning_chain()
