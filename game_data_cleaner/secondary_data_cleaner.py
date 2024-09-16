import pandas as pd
import os

from utils.local_file_handler import LocalFileHandler
from utils.s3_file_handler import S3FileHandler
from utils.processing_functions import (
    integer_reduce,
    save_file_local_first,
    load_file_local_first,
)

from config import CONFIGS

GAME_CONFIGS = CONFIGS["game"]
ENV = os.getenv("ENV", "dev")


class SecondaryDataCleaner:
    def __init__(self):
        self.game_mappings = LocalFileHandler().load_file(
            file_path="game_data_cleaner/game_mappings.json"
        )

    def secondary_cleaning_chain(self):
        (
            subcategories,
            mechanics_in_subcats_df,
            themes_in_subcats_df,
            big_cats_in_subcats_df,
        ) = self.clean_subcategories()
        mechanics = self.clean_mechanics(mechanics_in_subcats_df)
        themes = self.clean_themes(themes_in_subcats_df)
        games = self.add_subcat_categories_to_larger_categories(big_cats_in_subcats_df)
        designers = self.clean_designers()
        artists = self.clean_artists()
        publishers = self.clean_publishers()

        # We can save the Kaggle dataset to S3 here
        # self.s3_file_handler.save_file(
        #     file_path=GAME_CONFIGS["kaggle_games_file"], data=games_df
        # )

    def strip_low_entries(self, df, column_name, threshold):

        # remove designers with <3 games
        df_onehot = pd.get_dummies(df, columns=[column_name], drop_first=False).astype(
            int
        )

        # Step 1: Identify columns where the sum of their values is <= 3
        cols_with_low_sum = df_onehot.columns[df_onehot.sum(axis=0) <= threshold]

        # Step 2: Create the "Low Entries" column
        # If any column in a row has a sum <= 3, mark that row with 1
        df_onehot["Low Entries"] = (
            df_onehot[cols_with_low_sum].gt(0).any(axis=1).astype(int)
        )

        # Step 3: Drop columns where the sum is <= 3
        df = df_onehot.drop(columns=cols_with_low_sum).reset_index(drop=True)

        df.columns = df.columns.str.replace(f"{column_name}_", "")

        return df

    def clean_publishers(self):
        print("Cleaning Publishers")
        publishers = load_file_local_first(
            path=GAME_CONFIGS["dirty_dfs_directory"], file_name="publishers.pkl"
        )
        publishers = publishers.loc[publishers["boardgamepublisher"] != "(Uncredited)"]
        publishers = publishers.reset_index(drop=True)

        publishers = self.strip_low_entries(
            df=publishers, column_name="boardgamepublisher", threshold=3
        )

        save_file_local_first(
            path=GAME_CONFIGS["game_dfs_clean"],
            file_name="publishers.pkl",
            data=publishers,
        )

        return publishers

    def clean_artists(self):
        print("Cleaning Artists")
        artists = load_file_local_first(
            path=GAME_CONFIGS["dirty_dfs_directory"], file_name="artists.pkl"
        )
        artists = artists.loc[artists["boardgameartist"] != "(Uncredited)"]
        artists = artists.reset_index(drop=True)

        artists = self.strip_low_entries(
            df=artists, column_name="boardgameartist", threshold=3
        )

        save_file_local_first(
            path=GAME_CONFIGS["game_dfs_clean"],
            file_name="artists.pkl",
            data=artists,
        )

        return artists

    def clean_designers(self):
        print("Cleaning Designers")
        designers = load_file_local_first(
            path=GAME_CONFIGS["dirty_dfs_directory"], file_name="designers.pkl"
        )
        designers = designers.loc[designers["boardgamedesigner"] != "(Uncredited)"]
        designers = designers.reset_index(drop=True)

        designers = self.strip_low_entries(
            df=designers, column_name="boardgamedesigner", threshold=2
        )

        save_file_local_first(
            path=GAME_CONFIGS["game_dfs_clean"],
            file_name="designers.pkl",
            data=designers,
        )

        return designers

    def add_subcat_categories_to_larger_categories(self, big_cats_in_subcats_df):
        print("Adding Subcategories to Larger Categories")
        games = load_file_local_first(
            path=GAME_CONFIGS["game_dfs_clean"], file_name="games.pkl"
        )

        for key, value in self.game_mappings["big_category_mapper"].items():
            games.loc[
                games["BGGId"].isin(
                    big_cats_in_subcats_df.loc[
                        big_cats_in_subcats_df["boardgamecategory"] == key, "BGGId"
                    ]
                ),
                value,
            ] = 1
        return games

    def clean_mechanics(self, mechanics_in_subcats_df):
        print("Cleaning Mechanics")
        mechanics = load_file_local_first(
            path=GAME_CONFIGS["dirty_dfs_directory"], file_name="mechanics.pkl"
        )

        mechanics = mechanics.drop_duplicates(keep="first")
        mechanics["Count_Column"] = 1
        mechanics = mechanics.sort_values(by="BGGId").reset_index(drop=True)

        mechanics = mechanics.pivot_table(
            index="BGGId", columns="mechanic", values="Count_Column"
        ).copy()

        # Clean up mechanics
        # Here we are using our domain knowledge to compact several different catogories into one

        auction_list = mechanics[
            [x for x in mechanics.columns if "auction" in x.lower()]
        ].columns.to_list()

        drafting = mechanics[
            [x for x in mechanics.columns if "drafting" in x.lower()]
        ].columns.to_list()

        worker_placement = mechanics[
            [x for x in mechanics.columns if "worker" in x.lower()]
        ].columns.to_list()

        compacting_categories = {
            "Auction or Bidding": auction_list,
            "Drafting": drafting,
            "Worker Placement": worker_placement,
        }

        for category in compacting_categories:
            for item in compacting_categories[category]:
                mechanics.loc[mechanics[item] == 1, category] = 1
                mechanics = mechanics.drop([item], axis=1)

        mechanics.loc[mechanics["Legacy"] == 1, "Legacy Game"] = 1
        mechanics = mechanics.drop(["Legacy"], axis=1)

        turn_order_list = mechanics[
            [x for x in mechanics.columns if "turn order" in x.lower()]
        ].columns.to_list()

        mechanics = mechanics.drop(turn_order_list, axis=1)

        columns = mechanics.columns

        mechanics = integer_reduce(mechanics, columns, fill_value=0)

        mechanics = mechanics.reset_index().melt(
            id_vars="BGGId", var_name="mechanic", value_name="value"
        )
        mechanics = (
            mechanics[mechanics["value"] == 1]
            .drop("value", axis=1)
            .sort_values(by="BGGId")
            .reset_index(drop=True)
        )

        mechanics_in_subcats_df["boardgamecategory"] = mechanics_in_subcats_df[
            "boardgamecategory"
        ].map(self.game_mappings["actually_mechanics"])
        mechanics_in_subcats_df = mechanics_in_subcats_df.rename(
            columns={"boardgamecategory": "mechanic"}
        )

        mechanics = (
            pd.concat([mechanics, mechanics_in_subcats_df], axis=0)
            .sort_values(by="BGGId")
            .reset_index(drop=True)
        )

        save_file_local_first(
            path=GAME_CONFIGS["game_dfs_clean"],
            file_name="mechanics.pkl",
            data=mechanics,
        )

        return mechanics

    def clean_themes(self, themes_in_subcats_df):
        print("Cleaning Themes")
        themes = load_file_local_first(
            path=GAME_CONFIGS["dirty_dfs_directory"], file_name="themes.pkl"
        )

        themes = themes.dropna(subset=["Theme"]).sort_values("BGGId")

        themes_in_subcats_df = themes_in_subcats_df.rename(
            columns={"boardgamecategory": "Theme"}
        )

        themes = (
            pd.concat([themes, themes_in_subcats_df], axis=0)
            .sort_values(by="BGGId")
            .reset_index(drop=True)
        )

        save_file_local_first(
            path=GAME_CONFIGS["game_dfs_clean"],
            file_name="themes.pkl",
            data=themes,
        )

        return themes

    def clean_subcategories(self):
        print("Extracting Subcategories")

        subcategories = load_file_local_first(
            path=GAME_CONFIGS["dirty_dfs_directory"], file_name="subcategories.pkl"
        )

        subcategories = (
            subcategories.dropna(subset=["boardgamecategory"])
            .sort_values("BGGId")
            .reset_index(drop=True)
        )

        mechanics_in_subcats_df = subcategories[
            subcategories["boardgamecategory"].isin(
                self.game_mappings["actually_mechanics"].keys()
            )
        ].reset_index(drop=True)

        themes_in_subcats_df = subcategories[
            subcategories["boardgamecategory"].isin(
                self.game_mappings["actually_themes"]
            )
        ].reset_index(drop=True)

        big_cats_in_subcats_df = subcategories[
            subcategories["boardgamecategory"].isin(
                self.game_mappings["actually_major_categories"].keys()
            )
        ].reset_index(drop=True)

        # drop rows from subcategories where boardgamecategory is in list drop
        subcategories = subcategories[
            ~subcategories["boardgamecategory"].isin(
                self.game_mappings["drop_subcategories"]
            )
        ]
        subcategories = subcategories[
            ~subcategories["boardgamecategory"].isin(
                self.game_mappings["actually_mechanics"].keys()
            )
        ]
        subcategories = subcategories[
            ~subcategories["boardgamecategory"].isin(
                self.game_mappings["actually_subcategories"]
            )
        ].reset_index(drop=True)

        save_file_local_first(
            path=GAME_CONFIGS["game_dfs_clean"],
            file_name="subcategories.pkl",
            data=subcategories,
        )

        return (
            subcategories,
            mechanics_in_subcats_df,
            themes_in_subcats_df,
            big_cats_in_subcats_df,
        )


if __name__ == "__main__":
    cleaner = SecondaryDataCleaner()
    cleaner.secondary_cleaning_chain()
