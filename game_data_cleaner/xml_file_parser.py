from bs4 import BeautifulSoup
import pandas as pd
import os
import awswrangler as wr
import boto3
from bs4 import BeautifulSoup
from single_game_parser import GameEntryParser

ENV = os.environ.get("ENV", "dev")
S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")
DATA_DIRTY_PREFIX = os.environ.get("DATA_DIRTY_PREFIX")


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

        self.overall_dfs = {}

    def process_file_list(self):

        # list files in data dirty prefix in s3 using awswrangler
        file_list = wr.s3.list_objects(f"s3://{S3_SCRAPER_BUCKET}/{DATA_DIRTY_PREFIX}")

        #download items in file_list to local path


        for file in file_list:
            print(file)
            local_file_path = f"./raw_bgg_xml/{file.split("/")[-1]}"

            try:
                # open from local_pile_path
                local_open = open(local_file_path, encoding="utf8")
            except FileNotFoundError:
                # if ENV=="prod" then download the XML from S3
                print(f"Downloading {file} from S3")
                wr.s3.download(
                        path=file,
                        local_file=local_file_path,
                    )
                local_open = open(local_file_path, encoding="utf8")

            game_page = BeautifulSoup(local_open, features="xml")

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

                self.games_dfs.append(game_entry_df.dropna(axis=1))
                self.designers_dfs.append(designer_df.dropna(axis=1))
                self.categories_dfs.append(categories_hold_df.dropna(axis=1))
                self.mechanics_dfs.append(mechanic_df.dropna(axis=1))
                self.artists_dfs.append(artist_df.dropna(axis=1))
                self.publishers_dfs.append(publisher_df.dropna(axis=1))
                self.subcategories_dfs.append(category_df.dropna(axis=1))

        if self.games_dfs == []:
            return
        
        print(f"Len of games_dfs: {len(self.games_dfs)}\n\
              Len of designers_dfs: {len(self.designers_dfs)}\n\
                Len of categories_dfs: {len(self.categories_dfs)}\n\
                    Len of mechanics_dfs: {len(self.mechanics_dfs)}\n\
                        Len of artists_dfs: {len(self.artists_dfs)}\n\
                            Len of publishers_dfs: {len(self.publishers_dfs)}\n\
                                Len of subcategories_dfs: {len(self.subcategories_dfs)}")

        self.overall_dfs = {
            "games": pd.concat(self.games_dfs).reset_index(drop=True),
            "designers": pd.concat(self.designers_dfs).reset_index(drop=True),
            "categories": pd.concat(self.categories_dfs).reset_index(drop=True),
            "mechanics": pd.concat(self.mechanics_dfs).reset_index(drop=True),
            "artists": pd.concat(self.artists_dfs).reset_index(drop=True),
            "publishers": pd.concat(self.publishers_dfs).reset_index(drop=True),
            "subcategories": pd.concat(self.subcategories_dfs).reset_index(drop=True),
        }

    def _save_dfs_to_disk_or_s3(self):
        """Save all files as pkl files. Save to local drive in ENV==env, or
        copy pkl to s3 if ENV==prod"""

        for table_name, table in self.overall_dfs.items():
            if ENV == "dev":
                table.to_pickle(f"game_dfs_dirty/{table_name}.pkl")
            if ENV == "prod":
                table.to_pickle(f"{table_name}.pkl")
                wr.s3.upload(f"{table_name}.pkl", f"s3://{S3_SCRAPER_BUCKET}/game_dfs_dirty/{table_name}.pkl")

if __name__ == "__main__":

    file_parser = XMLFileParser()
    file_parser.process_file_list()
    file_parser._save_dfs_to_disk_or_s3()
