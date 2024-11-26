import gc
import os
from collections import defaultdict

import pandas as pd
from bs4 import BeautifulSoup
from single_game_parser import GameEntryParser

from config import CONFIGS
from modules.game_data_cleaner.games_data_cleaner import GameDataCleaner
from modules.game_data_cleaner.secondary_data_cleaner import SecondaryDataCleaner
from utils.processing_functions import (
    get_local_keys_based_on_env,
    get_s3_keys_based_on_env,
    load_file_local_first,
    save_file_local_first,
    save_to_aws_glue,
)

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
S3_SCRAPER_BUCKET = CONFIGS["s3_scraper_bucket"]
GAME_CONFIGS = CONFIGS["games"]
IS_LOCAL = True if os.environ.get("IS_LOCAL", "False").lower() == "true" else False


class DirtyDataExtractor:

    def __init__(self) -> None:
        pass

    def data_extraction_chain(self):
        file_list_to_process = self._get_file_list()
        raw_storage = self._process_file_list(file_list_to_process)
        dirty_storage = self._organize_raw_storage(raw_storage)
        self._save_dfs_to_disk_or_s3(dirty_storage)

    def _get_file_list(self) -> list[str]:
        # list files in data dirty prefix in s3 using awswrangler
        xml_directory = GAME_CONFIGS["output_xml_directory"]
        file_list_to_process = get_s3_keys_based_on_env(xml_directory)
        if not file_list_to_process:
            local_files = get_local_keys_based_on_env(xml_directory)
            file_list_to_process = [x for x in local_files if x.endswith(".xml")]
        print(file_list_to_process)
        return file_list_to_process

    def _process_file_list(self, file_list_to_process: list) -> dict[list]:
        """Process the list of files in the S3 bucket
        This function will process the list of files in the S3 bucket
        and extract the necessary information from the XML files. The
        function will return None."""

        raw_storage = {
            "games": [],
            "designers": [],
            "categories": [],
            "mechanics": [],
            "artists": [],
            "publishers": [],
            "subcategories": [],
            # "comments": [],
            "expansions": [],
        }

        for file in file_list_to_process:
            local_open = load_file_local_first(
                path=GAME_CONFIGS["output_xml_directory"],
                file_name=file.split("/")[-1],
            )

            game_page = BeautifulSoup(local_open, features="xml")

            game_entries = game_page.find_all("item")

            print(f"Number of game entries in file: {len(game_entries)}")

            if len(game_entries) == 0:
                print(
                    f"\n\nNo game entries found in file: {file}. Exiting application."
                )
                exit()

            for game_entry in game_entries:

                game_parser = GameEntryParser(game_entry=game_entry)

                if not game_parser.check_rating_count_threshold():
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
                    expansions,
                ) = game_parser.get_single_game_attributes()

                raw_storage["games"].append(game)
                raw_storage["designers"].append(designers)
                raw_storage["categories"].append(subcategories)
                raw_storage["mechanics"].append(mechanics)
                raw_storage["artists"].append(artists)
                raw_storage["publishers"].append(publishers)
                raw_storage["subcategories"].append(categories)
                raw_storage["expansions"].append(expansions)

        if not raw_storage["games"]:
            return

        return raw_storage

    def _organize_raw_storage(self, raw_storage: dict[list]) -> dict[pd.DataFrame]:
        print("Crafting data frames")

        dirty_storage = {}

        for table_name, list_of_entries in raw_storage.items():
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
                table = pd.DataFrame(list_of_entries)
                self._make_json_game_lookup_file(table)

            print(f"Deleting {table_name} from memory")
            del list_of_entries

            if None in table.columns:
                table = table.drop(columns=[None])
            else:
                pass

            table = table.sort_values(by="BGGId").reset_index(drop=True)

            dirty_storage[table_name] = table

        del raw_storage
        return dirty_storage

    def save_file_set(self, data, table):
        save_file_local_first(
            path=GAME_CONFIGS["dirty_dfs_directory"],
            file_name=f"{table}_dirty.pkl",
            data=data,
        )
        save_file_local_first(
            path=GAME_CONFIGS["dirty_dfs_directory"],
            file_name=f"{table}_dirty.csv",
            data=data,
        )
        if ENVIRONMENT == "prod":
            save_to_aws_glue(data=data, table=f"{table}_dirty")

    def _save_dfs_to_disk_or_s3(self, dirty_storage: dict[pd.DataFrame]):
        """Save all files as pkl files. Save to local drive in ENVIRONMENT==env, or
        copy pkl to s3 if ENVIRONMENT==prod"""

        for table_name, table in dirty_storage.items():

            print(f"Saving {table_name} to disk and uploading to S3")

            print(table.dtypes)

            save_file_local_first(
                path=GAME_CONFIGS["dirty_dfs_directory"],
                file_name=f"{table_name}.csv",
                data=table,
            )

            table = load_file_local_first(
                path=GAME_CONFIGS["dirty_dfs_directory"], file_name=f"{table_name}.csv"
            )

            print(table.dtypes)

            self.save_file_set(data=table, table=table_name)

            del table
            gc.collect()

    def _make_json_game_lookup_file(self, games_df: pd.DataFrame):

        games_df = games_df.copy()

        # lists of game ids and game names
        game_ids = list(games_df["BGGId"])
        game_names = list(games_df["Name"])

        game_id_lookup = dict(zip(game_ids, game_names))

        save_file_local_first(
            path="games", file_name="game_id_lookup.json", data=game_id_lookup
        )


if __name__ == "__main__":

    DirtyDataExtractor().data_extraction_chain()
    GameDataCleaner().primary_cleaning_chain()
    SecondaryDataCleaner().secondary_cleaning_chain()
