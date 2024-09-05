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
        pass

    def secondary_cleaning_chain(self):
        self.clean_mechanics()
        self.clean_themes()

    def clean_mechanics(self):
        mechanics = load_file_local_first(
            path=GAME_CONFIGS["dirty_dfs_directory"], file_name="mechanics.pkl"
        )
        print(mechanics.head())

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

        melted_df = mechanics.reset_index().melt(
            id_vars="BGGId", var_name="mechanic", value_name="value"
        )
        melted_df = (
            melted_df[melted_df["value"] == 1]
            .drop("value", axis=1)
            .sort_values(by="BGGId")
            .reset_index(drop=True)
        )

        save_file_local_first(
            path=GAME_CONFIGS["game_dfs_clean"],
            file_name="mechanics.pkl",
            data=melted_df,
        )

    def clean_themes(self):
        themes = load_file_local_first(
            path=GAME_CONFIGS["dirty_dfs_directory"], file_name="themes.pkl"
        )

        themes_expanded = pd.get_dummies(themes)
        theme_sort = pd.DataFrame(themes_expanded.sum().sort_values(ascending=False))
        themes_over_1 = list(theme_sort.loc[theme_sort[0] > 1].index)
        themes_attach = themes_expanded[themes_over_1]

        columns = themes_attach.columns

        themes_attach = integer_reduce(themes_attach, columns, fill_value=0)

        save_file_local_first(
            path=GAME_CONFIGS["game_dfs_clean"],
            file_name="themes.pkl",
            data=themes_attach,
        )

    def clean_subcategories(self):
        pass


if __name__ == "__main__":
    cleaner = SecondaryDataCleaner()
    cleaner.secondary_cleaning_chain()
