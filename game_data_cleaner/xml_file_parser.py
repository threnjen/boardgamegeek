from bs4 import BeautifulSoup
import pandas as pd
import os
import awswrangler as wr
from bs4 import BeautifulSoup
from game_data_cleaner.single_game_parser import GameEntryParser

ENV = os.environ.get("ENV", "dev")



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

    def process_file_list(self, file_list):

        for file in file_list:

            file_path = (
                f"game_data_scraper/scraped_games/{file}" if ENV == "dev" else file
            )

            # if ENV=="prod" then download the XML from S3
            if ENV == "prod":
                wr.s3.download(
                    path="s3://bucket/key",
                    local_file=f"game_data_scraper/scraped_games/{file}",
                )

            game_page = BeautifulSoup(open(file_path, encoding="utf8"), features="xml")

            # make entry for each game item on page
            game_entries = game_page.find_all("item")
            print(f"Number of game entries in this file: {len(game_entries)}")

            for game_entry in game_entries:
                game_parser = GameEntryParser(game_entry=game_entry)

                if not game_parser.check_rating_count_threshold():
                    print("Skipping game with low user ratings")
                    continue
                print(f"Processing game with ID: {game_entry['id']}")

                game_parser.parse_individual_game()
                (
                    game_entry_df,
                    categories_hold_df,
                    designer_df,
                    category_df,
                    mechanic_df,
                    artist_df,
                    publisher_df,
                ) = game_parser.get_one_game_dfs()

                self.games_dfs.append(game_entry_df)
                self.designers_dfs.append(designer_df)
                self.categories_dfs.append(categories_hold_df)
                self.mechanics_dfs.append(mechanic_df)
                self.artists_dfs.append(artist_df)
                self.publishers_dfs.append(publisher_df)
                self.subcategories_dfs.append(category_df)

        if self.games_dfs == []:
            return

        games = pd.concat(self.games_dfs)
        designers = pd.concat(self.designers_dfs)
        categories = pd.concat(self.categories_dfs)
        mechanics = pd.concat(self.mechanics_dfs)
        artists = pd.concat(self.artists_dfs)
        publishers = pd.concat(self.publishers_dfs)
        subcategories = pd.concat(self.subcategories_dfs)

        print(games.head())
        print(designers.head())
        print(categories.head())
        print(mechanics.head())
        print(artists.head())
        print(publishers.head())
        print(subcategories.head())
    


if __name__ == "__main__":

    file_list = [
        x for x in os.listdir("game_data_scraper/scraped_games") if x.endswith(".xml")
    ]

    XMLFileParser().process_file_list(file_list)
