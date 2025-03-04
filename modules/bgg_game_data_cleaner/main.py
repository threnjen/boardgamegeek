import gc
import os
from collections import defaultdict

import pandas as pd
from bs4 import BeautifulSoup
from single_game_parser import GameEntryParser

from config import CONFIGS
from modules.bgg_game_data_cleaner.games_data_cleaner import GameDataCleaner
from modules.bgg_game_data_cleaner.secondary_data_cleaner import SecondaryDataCleaner
from utils.processing_functions import (
    get_local_keys_based_on_env,
    get_s3_keys_based_on_env,
    load_file_local_first,
    save_file_local_first,
    save_to_aws_glue,
    save_dfs_to_disk_or_s3,
)

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
S3_SCRAPER_BUCKET = CONFIGS["s3_scraper_bucket"]
GAME_CONFIGS = CONFIGS["games"]
IS_LOCAL = True if os.environ.get("IS_LOCAL", "False").lower() == "true" else False


class DirtyDataExtractor:

    def __init__(self) -> None:
        pass

    def data_extraction_chain(self):
        xml_files_to_process = self._get_raw_xml_file_keys()
        raw_storage = self._process_raw_xml_files(xml_files_to_process)
        dirty_game_data_frames = self._create_dirty_data_frames(raw_storage)
        self._save_dirty_dfs(dirty_game_data_frames)

    def _get_raw_xml_file_keys(self) -> list[str]:
        """Get the list of S3 file keys of raw xml to process.
        The function will return a list of keys from the prod S3 bucket if the ENVIRONMENT is set to prod.
        The function will return a list of keys from the dev S3 bucket if the ENVIRONMENT is set to dev.
        If there are no keys in the S3 bucket, the function will return a list of local files in the dev directory.
        """
        # list files in data dirty prefix in s3 using awswrangler
        xml_directory = GAME_CONFIGS["output_xml_directory"]
        xml_files_to_process = get_s3_keys_based_on_env(xml_directory)
        if not xml_files_to_process:
            local_files = get_local_keys_based_on_env(xml_directory)
            xml_files_to_process = [x for x in local_files if x.endswith(".xml")]
        return xml_files_to_process

    def _process_raw_xml_files(self, xml_files_to_process: list) -> dict[list]:
        """Process the list of files in the S3 bucket
        This function will process the list of files in the S3 bucket
        and extract the necessary information from the XML files.
        The function will return a dictionary with the following keys:
        - games: list of game entries
        - designers: list of designer entries
        - categories: list of category entries
        - mechanics: list of mechanic entries
        - artists: list of artist entries
        - publishers: list of publisher entries
        - subcategories: list of subcategory entries
        - expansions: list of expansion entries
        """
        print("\nProcessing raw XML files")

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

        for file in xml_files_to_process:
            local_open = load_file_local_first(
                path=GAME_CONFIGS["output_xml_directory"],
                file_name=file.split("/")[-1],
            )

            game_page = BeautifulSoup(local_open, features="xml")

            game_entries = game_page.find_all("item")

            print(
                f"Number of game entries in file {file.split("/")[-1]}: {len(game_entries)}"
            )

            if len(game_entries) == 0:
                print(f"\n\nNo game entries found in file {file}. Exiting application.")
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

        print(raw_storage.keys())
        return raw_storage

    def _create_dirty_data_frames(self, raw_storage: dict[list]) -> dict[pd.DataFrame]:
        """Create data frames from the raw storage dictionary
        This function will create data frames from the raw storage dictionary
        and return a dictionary with the following keys:
        - games: data frame of game entries
        - designers: data frame of designer entries
        - categories: data frame of category entries
        - mechanics: data frame of mechanic entries
        - artists: data frame of artist entries
        - publishers: data frame of publisher entries
        - subcategories: data frame of subcategory entries
        - expansions: data frame of expansion entries
        """
        print("\nCrafting data frames")

        dirty_game_data_frames = {}

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

            dirty_game_data_frames[table_name] = table

        del raw_storage

        print(dirty_game_data_frames.keys())
        return dirty_game_data_frames

    def _save_dirty_dfs(self, dirty_game_data_frames: dict[pd.DataFrame]):
        """Save all files as pkl files. Save to local drive in ENVIRONMENT==dev, or
        copy pkl to s3 if ENVIRONMENT==prod"""

        print("\nSaving data frames to disk or S3")

        for table_name, table in dirty_game_data_frames.items():

            print(f"Saving {table_name} to disk and uploading to S3")

            save_dfs_to_disk_or_s3(
                df=table,
                table_name=f"{table_name}_dirty",
                path=GAME_CONFIGS["dirty_dfs_directory"],
            )

            del table
            gc.collect()

    def _make_json_game_lookup_file(self, games_df: pd.DataFrame):
        """Make a json file with game ids and game names for lookup"""

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
