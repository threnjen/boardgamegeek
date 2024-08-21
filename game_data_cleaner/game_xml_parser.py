from bs4 import BeautifulSoup
import re
import json
import pandas as pd
import os
import awswrangler as wr
from bs4 import BeautifulSoup
from typing import Optional
from game_data_cleaner.game_data_cleaner import GameEntryParser

ENV = os.environ.get("ENV", "dev")


class GameXMLParser:

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
            parse_xml_file(filename=file)

        self.games_dfs.append(this_game)
        self.designers_dfs.append(designer)
        self.categories_dfs.append(category)
        self.mechanics_dfs.append(mechanic)
        self.artists_dfs.append(artist)
        self.publishers_dfs.append(publisher)
        self.subcategories_dfs.append(categories_hold)

    # if games_dfs == []:
    #     continue
    # games = pd.concat(games_dfs)
    # designers = pd.concat(designers_dfs)
    # categories = pd.concat(categories_dfs)
    # mechanics = pd.concat(mechanics_dfs)
    # artists = pd.concat(artists_dfs)
    # publishers = pd.concat(publishers_dfs)
    # subcategories = pd.concat(subcategories_dfs)

    # games.to_pickle(f"data_store/data_dirty/scraped_games_processed/games{str(file_suffix)}.pkl")
    # designers.to_pickle(
    #     f"data_store/data_dirty/scraped_games_processed/designers{str(file_suffix)}.pkl"
    # )
    # categories.to_pickle(
    #     f"data_store/data_dirty/scraped_games_processed/categories{str(file_suffix)}.pkl"
    # )
    # mechanics.to_pickle(
    #     f"data_store/data_dirty/scraped_games_processed/mechanics{str(file_suffix)}.pkl"
    # )
    # artists.to_pickle(
    #     f"data_store/data_dirty/scraped_games_processed/artists{str(file_suffix)}.pkl"
    # )
    # publishers.to_pickle(
    #     f"data_store/data_dirty/scraped_games_processed/publishers{str(file_suffix)}.pkl"
    # )
    # subcategories.to_pickle(
    #     f"data_store/data_dirty/scraped_games_processed/subcategories{str(file_suffix)}.pkl"
    # )

    def parse_xml_file(
        self, game_page: Optional[BeautifulSoup] = None, filename: Optional[str] = None
    ) -> BeautifulSoup:

        file_path = (
            f"game_data_scraper/scraped_games/{filename}" if ENV == "dev" else filename
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
            if not check_rating_count_threshold(game_entry):
                continue
            game_dict = GameEntryParser().parse_individual_game(game_entry)

    def check_rating_count_threshold(self, game: BeautifulSoup) -> bool:
        user_ratings = int(find_thing_in_soup(game, "usersrated"))
        if user_ratings < MIN_USER_RATINGS:
            return False
        return True


if __name__ == "__main__":
    GameXMLParser().process_file_list()
