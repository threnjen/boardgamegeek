from bs4 import BeautifulSoup
import re
import json
import pandas as pd
import os
import awswrangler as wr
from bs4 import BeautifulSoup
from typing import Optional
from game_data_cleaner.single_game_parser import GameEntryParser

ENV = os.environ.get("ENV", "dev")
MIN_USER_RATINGS = 10


class XMLFileParser:

    def __init__(self) -> None:
        self.games_dfs = []
        self.designers_dfs = []
        self.categories_dfs = []
        self.mechanics_dfs = []
        self.artists_dfs = []
        self.publishers_dfs = []
        self.subcategories_dfs = []
        self.comments_dfs = []

    def process_file_list(self):

        file_list = [
            x
            for x in os.listdir("game_data_scraper/scraped_games")
            if x.endswith(".xml")
        ]

        for file in file_list:
            file_path = (
                f"game_data_scraper/scraped_games/{filename}"
                if ENV == "dev"
                else filename
            )

            # if ENV=="prod" then download the XML from S3
            if ENV == "prod":
                wr.s3.download(
                    path="s3://bucket/key",
                    local_file=f"game_data_scraper/scraped_games/{filename}",
                )

            game_page = BeautifulSoup(open(file_path, encoding="utf8"), features="xml")

            # make entry for each game item on page
            game_entries = game_page.find_all("item")
            print(f"Number of game entries in this file: {len(game_entries)}")

            for game_entry in game_entries:
                if not self.check_rating_count_threshold(game_entry):
                    continue
                game_parser = GameEntryParser(game_entry=game_entry)
                game_parser.parse_individual_game()
                (
                    game_entry_df,
                    categories_hold_df,
                    designer_df,
                    category_df,
                    mechanic_df,
                    artist_df,
                    publisher_df,
                ) = game_parser.get_all_dfs()

                self.games_dfs.append(game_entry_df)
                self.designers_dfs.append(designer_df)
                self.categories_dfs.append(categories_hold_df)
                self.mechanics_dfs.append(mechanic_df)
                self.artists_dfs.append(artist_df)
                self.publishers_dfs.append(publisher_df)
                self.subcategories_dfs.append(category_df)

        if self.games_dfs == []:
            return

        self.games = pd.concat(self.games_dfs)
        self.designers = pd.concat(self.designers_dfs)
        self.categories = pd.concat(self.categories_dfs)
        self.mechanics = pd.concat(self.mechanics_dfs)
        self.artists = pd.concat(self.artists_dfs)
        self.publishers = pd.concat(self.publishers_dfs)
        self.subcategories = pd.concat(self.subcategories_dfs)

    def check_rating_count_threshold(self, game: BeautifulSoup) -> bool:
        user_ratings = int(GameEntryParser().find_thing_in_soup(game, "usersrated"))

        if user_ratings < MIN_USER_RATINGS:
            return False
        return True


if __name__ == "__main__":
    XMLFileParser().process_file_list()
