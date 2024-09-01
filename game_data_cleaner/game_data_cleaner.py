import pandas as pd
import numpy as np
import requests
import regex as re
import time
import os
import gc
import json

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


class GameDataCleaner:

    def __init__(self) -> None:
        self.s3_file_handler = S3FileHandler()
        self.local_handler = LocalFileHandler()

    def cleaning_chain(self) -> pd.DataFrame:
        games_df = self.load_games_data("data/game_dfs_dirty/games.pkl")
        games_df = self._drop_duplicates(games_df)
        games_df = self._drop_unneeded_columns(games_df)
        games_df = self._clean_best_players(games_df)
        games_df = self._add_binary_flags(games_df)
        print(games_df.info())

    def load_games_data(self, file_path: str) -> pd.DataFrame:
        """Load games data from a file path"""
        games_df = self.local_handler.load_pkl(file_path)
        return games_df

    def _drop_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df = df.drop_duplicates(subset="BGGId", keep="first")
        return df

    def _drop_unneeded_columns(self, df: pd.DataFrame) -> pd.DataFrame:

        df = df.copy()

        # TO DO - PUT THIS IN THE CONFIG FILE
        drop_columns = [
            "NumAwards",
            "NumFans",
            "NumPageViews",
            "RulesPosts",
            "TotalPosts",
            "Category",
            "IsExpansion",
            "Rank:rpgitem",
            "Rank:boardgameaccessory",
            "Rank:videogame",
            "Rank:amiga",
            "Rank:commodore64",
            "Rank:arcade",
            "Rank:atarist",
            "Setting",
            "Mechanism",
        ]

        # drop non-boardgame related information
        for column in drop_columns:
            if column in df.columns:
                df = df.drop(column, axis=1)

        return df

    def _clean_best_players(self, df):
        df = df.copy()
        print(df["BestPlayers"].head())

        # fill in missing values with 0
        df["BestPlayers"] = df["BestPlayers"].fillna("0")

        # strip out any "+" from strings and leave only integers
        df["BestPlayers"] = df["BestPlayers"].apply(lambda x: re.sub(r"\+", "", x))

        # change the datatype of BestPlayers to int8
        df["BestPlayers"] = df["BestPlayers"].astype("int8")

        return df

    def _add_binary_flags(self, df):
        df = df.copy()

        # TO DO - PUT THIS IN THE CONFIG FILE
        # add a binary flag for games that are expansions
        df.loc[df["Rank:thematic"].notna(), "Cat:Thematic"] = 1
        df.loc[df["Rank:strategygames"].notna(), "Cat:Strategy"] = 1
        df.loc[df["Rank:wargames"].notna(), "Cat:War"] = 1
        df.loc[df["Rank:familygames"].notna(), "Cat:Family"] = 1
        df.loc[df["Rank:cgs"].notna(), "Cat:CGS"] = 1
        df.loc[df["Rank:abstracts"].notna(), "Cat:Abstract"] = 1
        df.loc[df["Rank:partygames"].notna(), "Cat:Party"] = 1
        df.loc[df["Rank:childrensgames"].notna(), "Cat:Childrens"] = 1

        return df


if __name__ == "__main__":
    cleaner = GameDataCleaner().cleaning_chain()
