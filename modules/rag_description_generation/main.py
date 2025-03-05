import gc
import json
import os
import sys
import time

import boto3
import pandas as pd
from pydantic import BaseModel, ConfigDict

from config import CONFIGS

# from modules.rag_description_generation.ec2_weaviate import Ec2
from modules.rag_description_generation.rag_dynamodb import DynamoDB
from modules.rag_description_generation.rag_functions import (
    get_single_game_entries,
    prompt_replacement,
)
from utils.processing_functions import load_file_local_first
from utils.weaviate_client import WeaviateClient

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
S3_SCRAPER_BUCKET = CONFIGS["s3_scraper_bucket"]
GAME_CONFIGS = CONFIGS["games"]
RATINGS_CONFIGS = CONFIGS["ratings"]
IS_LOCAL = True if os.environ.get("IS_LOCAL", "False").lower() == "true" else False


class RagDescription(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    start_block: str
    end_block: str
    num_completed_games: int = 0
    collection_name: str = ""
    ip_address: str = None
    overall_stats: dict = {}
    game_ids: list = []
    generate_prompt: str = None
    weaviate: WeaviateClient = None
    dynamodb_client: DynamoDB = None

    def model_post_init(self, __context):
        self.collection_name = f"reviews_{self.start_block}_{self.end_block}"
        self.start_block = int(self.start_block)
        self.end_block = int(self.end_block)
        self.num_completed_games = self.start_block

    # def confirm_running_ec2_host(self):
    #     ec2_instance = Ec2()
    #     ec2_instance.validate_ready_weaviate_instance()
    #     self.ip_address = ec2_instance.get_ip_address()
    #     ec2_instance.copy_docker_compose_to_instance()
    #     ec2_instance.start_docker()

    #     print(f"\nWeaviate instance running at {self.ip_address}")

    # def stop_ec2_instance(self):
    #     ec2_instance = Ec2()
    #     self.ip_address = ec2_instance.get_ip_address()
    #     ec2_instance.stop_instance()

    # def compute_game_overall_stats(self, game_df):
    #     overall_mean = round(game_df["AvgRating"].describe()["mean"], 2)
    #     game_std = round(game_df["AvgRating"].describe()["std"], 2)

    #     self.overall_stats["overall_mean"] = overall_mean
    #     self.overall_stats["overall_std"] = game_std
    #     self.overall_stats["two_under"] = round(overall_mean - 2 * game_std, 2)
    #     self.overall_stats["one_under"] = round(overall_mean - game_std, 2)
    #     self.overall_stats["half_over"] = round(overall_mean + 0.5 * game_std, 2)
    #     self.overall_stats["one_over"] = round(overall_mean + game_std, 2)

    #     print(f"Overall mean: {overall_mean}")

    def get_overall_stats(self):
        dynamodb_client = boto3.client("dynamodb")
        response = dynamodb_client.get_item(
            TableName=CONFIGS["dynamodb_game_stats_table_name"],
            Key={
                "game_id": {
                    "S": "all_stats",
                },
            },
        )

        self.overall_stats["overall_mean"] = response["Item"]["overall_mean"]["N"]
        self.overall_stats["overall_std"] = response["Item"]["overall_std"]["N"]
        self.overall_stats["two_under"] = response["Item"]["two_under"]["N"]
        self.overall_stats["one_under"] = response["Item"]["one_under"]["N"]
        self.overall_stats["half_over"] = response["Item"]["half_over"]["N"]
        self.overall_stats["one_over"] = response["Item"]["one_over"]["N"]

    def load_reduced_game_df(self):
        print(f"\nLoading game data from {GAME_CONFIGS['clean_dfs_directory']}")
        game_df = load_file_local_first(
            path=GAME_CONFIGS["clean_dfs_directory"], file_name="games_clean.pkl"
        )

        self.get_overall_stats()

        game_df_reduced = game_df.sort_values("BayesAvgRating", ascending=False)[
            self.start_block : self.end_block
        ]

        self.game_ids = game_df_reduced["BGGId"].astype(str).tolist()

        game_df_reduced = game_df_reduced[["BGGId", "Name", "Description", "AvgRating"]]

        del game_df
        gc.collect()
        print("Loaded and refined games data")

        return game_df_reduced

    def merge_game_df_with_ratings_df(self, game_df_reduced):
        print(f"\nLoading user ratings from {RATINGS_CONFIGS['dirty_dfs_directory']}")
        ratings_df = load_file_local_first(
            path=RATINGS_CONFIGS["dirty_dfs_directory"],
            file_name="ratings_data.pkl",
        )
        ratings_df = ratings_df[["username", "BGGId", "rating", "value"]]

        print("Loaded user ratings data")

        print(
            f"Reducing user ratings to only include games in the reduced game dataframe\n"
        )
        all_games_df = ratings_df.merge(
            game_df_reduced,
            on="BGGId",
            how="inner",
        )

        all_games_df["BGGId"] = all_games_df["BGGId"].astype(str)

        del game_df_reduced
        del ratings_df
        gc.collect()

        return all_games_df

    def load_prompt(self):
        return json.loads(
            open("modules/rag_description_generation/prompt.json").read()
        )["gpt4o_mini_generate_prompt_structured"]

    def process_single_game(
        self,
        weaviate_client: WeaviateClient,
        game_id: str,
        all_games_df: pd.DataFrame,
        generate_prompt: str,
    ):
        if not self.dynamodb_client.check_dynamo_db_key(game_id=game_id):
            df, game_name, game_mean = get_single_game_entries(
                df=all_games_df, game_id=game_id, sample_pct=0.1
            )
            reviews = df["combined_review"].to_list()
            # vectors = df["embedding"].to_list()
            weaviate_client.add_reviews_collection_batch(
                collection_name=self.collection_name,
                game_id=game_id,
                reviews=reviews,  # , vectors=vectors
            )
            current_prompt = prompt_replacement(
                current_prompt=generate_prompt,
                overall_stats=self.overall_stats,
                game_name=game_name,
                game_mean=game_mean,
            )
            summary = weaviate_client.generate_aggregated_review(
                game_id=game_id,
                collection_name=self.collection_name,
                generate_prompt=current_prompt,
            )
            self.dynamodb_client.divide_and_process_generated_summary(
                game_id, summary=summary.generated
            )
            # print(f"\n{summary.generated}")
            # weaviate_client.remove_collection_items(game_id=game_id, reviews=reviews)
            return

        print(f"Game {game_id} already processed")

    def rag_description_generation_chain(self):
        # self.confirm_running_ec2_host()
        game_df_reduced = self.load_reduced_game_df()
        all_games_df = self.merge_game_df_with_ratings_df(game_df_reduced)
        generate_prompt = self.load_prompt()

        weaviate_client = WeaviateClient(
            # ip_address=self.ip_address,
        )
        weaviate_client.create_reviews_collection(collection_name=self.collection_name)

        self.dynamodb_client = DynamoDB()

        for game_id in self.game_ids:
            print(
                f"\nProcessing game {game_id}\n{self.num_completed_games} of {self.end_block}"
            )
            self.process_single_game(
                weaviate_client, game_id, all_games_df, generate_prompt
            )
            self.num_completed_games += 1

        weaviate_client.close_client()


if __name__ == "__main__":

    start_block = sys.argv[1]
    end_block = sys.argv[2]

    print(start_block, end_block)

    rag_description = RagDescription(start_block=start_block, end_block=end_block)
    rag_description.rag_description_generation_chain()
