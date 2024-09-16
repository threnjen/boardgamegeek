import gc
import os
from collections import defaultdict

import pandas as pd
from bs4 import BeautifulSoup
from single_game_parser import GameEntryParser

from config import CONFIGS
from game_data_cleaner.primary_data_cleaner import GameDataCleaner
from game_data_cleaner.secondary_data_cleaner import SecondaryDataCleaner
from utils.processing_functions import load_file_local_first, save_file_local_first
from utils.s3_file_handler import S3FileHandler

ENV = os.environ.get("ENV", "dev")
S3_SCRAPER_BUCKET = CONFIGS["s3_scraper_bucket"]
GAME_CONFIGS = CONFIGS["game"]
IS_LOCAL = True if os.environ.get("IS_LOCAL", "False") == "True" else False


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
            "expansions": [],
        }

    def game_cleaning_chain(self):
        self._process_file_list()
        self._save_dfs_to_disk_or_s3()

    def _process_file_list(self):
        """Process the list of files in the S3 bucket
        This function will process the list of files in the S3 bucket
        and extract the necessary information from the XML files. The
        function will return None."""

        # list files in data dirty prefix in s3 using awswrangler
        file_list = S3FileHandler().list_files(GAME_CONFIGS["output_xml_directory"])
        if not file_list:
            local_files = os.listdir(f"data/{GAME_CONFIGS['output_xml_directory']}")
            file_list = [x for x in local_files if x.endswith(".xml")]

        # download items in file_list to local path

        for file in file_list:
            print(file)
            local_open = load_file_local_first(
                path=GAME_CONFIGS["output_xml_directory"],
                file_name=file.split("/")[-1],
            )

            game_page = BeautifulSoup(local_open, features="xml")

            # make entry for each game item on page
            game_entries = game_page.find_all("item")
            # print(f"Number of game entries in this file: {len(game_entries)}")

            for game_entry in game_entries:
                game_parser = GameEntryParser(game_entry=game_entry)

                if not game_parser.check_rating_count_threshold():
                    # print("Skipping game with low user ratings")
                    continue
                print(f"Processing game with ID: {game_entry['id']}")

                game_parser.parse_individual_game()
                (
                    game,
                    subcategories,
                    designers,
                    categories,
                    mechanics,
                    artists,
                    publishers,
                    expansions,
                ) = game_parser.get_single_game_attributes()

                self.entry_storage["games"].append(game.dropna(axis=1))
                self.entry_storage["designers"].append(designers)
                self.entry_storage["categories"].append(subcategories)
                self.entry_storage["mechanics"].append(mechanics)
                self.entry_storage["artists"].append(artists)
                self.entry_storage["publishers"].append(publishers)
                self.entry_storage["subcategories"].append(categories)
                self.entry_storage["expansions"].append(expansions)

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
                self._make_json_game_lookup_file(table)

            print(f"Deleting {table_name} from memory")
            del list_of_entries

            print(f"Saving {table_name} to disk and uploading to S3")

            save_file_local_first(
                path=GAME_CONFIGS["dirty_dfs_directory"],
                file_name=f"{table_name}.pkl",
                data=table,
            )

            del table
            gc.collect()

    def _make_json_game_lookup_file(self, games_df: pd.DataFrame):

        games_df = games_df.copy()

        # lists of game ids and game names
        game_ids = list(games_df["BGGId"])
        game_names = list(games_df["Name"])

        game_id_lookup = dict(zip(game_ids, game_names))

        S3FileHandler().save_file(
            file_path=GAME_CONFIGS["game_id_lookup_file"], data=game_id_lookup
        )


if __name__ == "__main__":

    file_parser = XMLFileParser()
    file_parser.game_cleaning_chain()
    GameDataCleaner().primary_cleaning_chain()
    SecondaryDataCleaner().secondary_cleaning_chain()
