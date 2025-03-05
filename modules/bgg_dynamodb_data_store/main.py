import logging
import os
from datetime import datetime

import boto3
import pandas as pd
import numpy as np
from pydantic import BaseModel, ConfigDict

from config import CONFIGS
from utils.processing_functions import load_file_local_first

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
S3_SCRAPER_BUCKET = CONFIGS["s3_scraper_bucket"]
GAME_CONFIGS = CONFIGS["games"]
RATINGS_CONFIGS = CONFIGS["ratings"]
IS_LOCAL = True if os.environ.get("IS_LOCAL", "False").lower() == "true" else False

logger = logging.getLogger(__name__)


class DynamoDBDataWriter(BaseModel):
    """
    Class to handle writing data to DynamoDB.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
    )

    dynamodb_client: boto3.client = boto3.client("dynamodb")
    game_df: pd.DataFrame = pd.DataFrame()
    ratings_df: pd.DataFrame = pd.DataFrame()
    overall_stats: dict = {}

    def model_post_init(self, __context):
        """
        Post-initialization method to set up the DynamoDB client.
        """
        pass

    def calculate_all_game_stats(self):
        """
        Calculate the overall and individual game stats and write them to DynamoDB.
        """

        self.game_df = load_file_local_first(
            path=GAME_CONFIGS["clean_dfs_directory"], file_name="games_clean.pkl"
        )

        self.ratings_df = load_file_local_first(
            path=RATINGS_CONFIGS["dirty_dfs_directory"],
            file_name="ratings_data.pkl",
        )

        print(len(self.game_df))

        self.calculate_overall_stats()

        self.calculate_individual_stats()

        self.fill_table()

        return True

    def calculate_overall_stats(self):
        """Calculate the overall game stats."""
        print("Calculating overall game stats")

        overall_mean = round(self.game_df["AvgRating"].describe()["mean"], 2)
        game_std = round(self.game_df["AvgRating"].describe()["std"], 2)

        print(overall_mean)

        self.overall_stats["all_stats"] = {
            "overall_mean": overall_mean,
            "overall_std": game_std,
            "two_under": round(overall_mean - 2 * game_std, 2),
            "one_under": round(overall_mean - game_std, 2),
            "half_over": round(overall_mean + 0.5 * game_std, 2),
            "one_over": round(overall_mean + game_std, 2),
        }

    def calculate_individual_stats(self):
        """Calculate the individual game stats."""
        print("Calculating individual game stats")
        game_ids = self.game_df["BGGId"].tolist()

        for game_id in game_ids:
            single_game_entry = self.ratings_df[
                self.ratings_df["BGGId"] == game_id
            ].copy()

            overall_mean = round(single_game_entry["rating"].describe()["mean"], 2)

            if np.isnan(overall_mean):
                print(f"Game {game_id} has no ratings. Skipping.")
                continue

            game_std = round(single_game_entry["rating"].describe()["std"], 2)

            self.overall_stats[game_id] = {
                "overall_mean": overall_mean,
                "overall_std": game_std,
                "two_under": round(overall_mean - 2 * game_std, 2),
                "one_under": round(overall_mean - game_std, 2),
                "half_over": round(overall_mean + 0.5 * game_std, 2),
                "one_over": round(overall_mean + game_std, 2),
            }

    def fill_table(self):
        """Fill the DynamoDB table with the calculated stats."""

        table_name = (
            CONFIGS["dynamodb_game_stats_table_name"]
            if ENVIRONMENT == "prod"
            else f'dev_{CONFIGS["dynamodb_game_stats_table_name"]}'
        )

        print(f"Writing to DynamoDB table {table_name}")

        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(table_name)

        with table.batch_writer() as writer:
            for key, item in self.overall_stats.items():
                dynamodb_item = {}
                dynamodb_item["game_id"] = str(key)
                dynamodb_item.update({item: str(value) for item, value in item.items()})
                dynamodb_item["updated_at"] = datetime.utcnow().strftime("%Y%m%d")
                writer.put_item(Item=dynamodb_item)

        logger.info(f"Loaded {len(self.overall_stats)} games into table {table_name}")


if __name__ == "__main__":
    dynamodb_writer = DynamoDBDataWriter()

    dynamodb_writer.calculate_all_game_stats()
