from bs4 import BeautifulSoup
import pandas as pd
import os
import awswrangler as wr
import boto3
import gc
from bs4 import BeautifulSoup
from single_game_parser import GameEntryParser
from collections import defaultdict

ENV = os.environ.get("ENV", "dev")
S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")
DATA_DIRTY_PREFIX = os.environ.get("DATA_DIRTY_PREFIX")


class XMLFileParser:

    def __init__(self) -> None:

        self.entry_storage = {
            "games": [],
            "designers": [],
            "categories": [],
            "mechanics": [],
            "artists": [],
            "publishers": [],
            "subcategories": [],
            "comments": [],
        }

    def process_file_list(self):

        # list files in data dirty prefix in s3 using awswrangler
        file_list = wr.s3.list_objects(f"s3://{S3_SCRAPER_BUCKET}/{DATA_DIRTY_PREFIX}")

        # download items in file_list to local path

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
            # print(f"Number of game entries in this file: {len(game_entries)}")

            for game_entry in game_entries:
                game_parser = GameEntryParser(game_entry=game_entry)

                if not game_parser.check_rating_count_threshold():
                    # print("Skipping game with low user ratings")
                    continue
                # print(f"Processing game with ID: {game_entry['id']}")

                game_parser.parse_individual_game()
                (
                    game,
                    subcategories,
                    designers,
                    categories,
                    mechanics,
                    artists,
                    publishers,
                ) = game_parser.get_single_game_attributes()

                self.entry_storage['games'].append(game.dropna(axis=1))
                self.entry_storage['designers'].append(designers)
                self.entry_storage['categories'].append(subcategories)
                self.entry_storage['mechanics'].append(mechanics)
                self.entry_storage['artists'].append(artists)
                self.entry_storage['publishers'].append(publishers)
                self.entry_storage['subcategories'].append(categories)

        if not self.entry_storage["games"]:
            return

    def _save_dfs_to_disk_or_s3(self):
        """Save all files as pkl files. Save to local drive in ENV==env, or
        copy pkl to s3 if ENV==prod"""

        print("Crafting data frames")

        for table_name, list_of_entries in self.entry_storage.items():
            print(f"Len of {table_name}: {len(list_of_entries)}")

            if not list_of_entries:
                continue

            print(f"Creating table for {table_name}")
            if table_name != "games":
                combined_entries = defaultdict(list)
                for d in list_of_entries:
                    for key, value in d.items():
                        combined_entries[key].extend(value)
                list_of_entries = dict(combined_entries)
                table = pd.DataFrame.from_dict(list_of_entries)
            else:
                table = pd.concat(list_of_entries, ignore_index=True)


            print(f"Deleting {table_name} from memory")
            del list_of_entries

            print(f"Saving {table_name} to disk and uploading to S3")
            if ENV == "dev":
                table.to_pickle(f"game_dfs_dirty/{table_name}.pkl")
            if ENV == "prod":
                table.to_pickle(f"{table_name}.pkl")
                wr.s3.upload(
                    f"{table_name}.pkl",
                    f"s3://{S3_SCRAPER_BUCKET}/game_dfs_dirty/{table_name}.pkl",
                )

            del table
            gc.collect()


if __name__ == "__main__":

    file_parser = XMLFileParser()
    file_parser.process_file_list()
    file_parser._save_dfs_to_disk_or_s3()