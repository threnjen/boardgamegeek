import json
import os
import sys

import boto3
from boto3.dynamodb.conditions import Key
from pydantic import BaseModel, ConfigDict

from config import CONFIGS

from modules.rag_description_generation.rag_dynamodb import RagDynamoDB
from modules.rag_description_generation.rag_functions import (
    get_single_game_reviews,
    prompt_replacement,
)
from utils.processing_functions import load_file_local_first
from modules.rag_description_generation.weaviate_client import WeaviateClient

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
    dynamodb_rag_client: RagDynamoDB = None
    dynamodb_client: boto3.client = None

    def model_post_init(self, __context):
        self.collection_name = f"reviews_{self.start_block}_{self.end_block}"
        self.start_block = int(self.start_block)
        self.end_block = int(self.end_block)
        self.num_completed_games = self.start_block
        self.dynamodb_client = boto3.client("dynamodb")

    def get_overall_stats(self):

        response = self.dynamodb_client.get_item(
            TableName=CONFIGS["dynamodb"]["game_stats_table"],
            Key={
                "game_id": {
                    "S": "all_stats",
                },
            },
        )["Item"]

        self.overall_stats["overall_mean"] = float(response["overall_mean"]["S"])
        self.overall_stats["overall_std"] = float(response["overall_std"]["S"])
        self.overall_stats["two_under"] = float(response["two_under"]["S"])
        self.overall_stats["one_under"] = float(response["one_under"]["S"])
        self.overall_stats["half_over"] = float(response["half_over"]["S"])
        self.overall_stats["one_over"] = float(response["one_over"]["S"])

    def get_game_ids(self):
        print(f"\nLoading game data from {GAME_CONFIGS['clean_dfs_directory']}")

        game_avg_ratings = load_file_local_first(
            path="games", file_name="game_avg_ratings.json"
        )[self.start_block : self.end_block]
        game_ids = [str(x[0]) for x in game_avg_ratings]

        return game_ids

    def get_game_mean_rating(self, game_id):

        table_name = CONFIGS["dynamodb"]["game_stats_table"]

        response = self.dynamodb_client.get_item(
            TableName=table_name,
            Key={
                "game_id": {
                    "S": game_id,
                },
            },
        )["Item"]

        return float(response["overall_mean"]["S"])

    def get_game_ratings(self, game_id):

        table_name = CONFIGS["dynamodb"]["game_individual_ratings_table"]

        dynamodb_resource = boto3.resource("dynamodb")
        table = dynamodb_resource.Table(table_name)

        filtering_exp = Key("game_id").eq(game_id)
        resp = table.query(KeyConditionExpression=filtering_exp)
        return resp.get("Items")

    def create_single_game_data(self, game_id: str) -> tuple:
        game_mean_rating = self.get_game_mean_rating(game_id)
        game_ratings = self.get_game_ratings(game_id)

        return game_mean_rating, game_ratings

    def load_prompt(self):
        return json.loads(
            open("modules/rag_description_generation/prompt.json").read()
        )["gpt4o_mini_generate_prompt_structured"]

    def process_single_game(
        self,
        weaviate_client: WeaviateClient,
        game_id: str,
        game_ratings: dict,
        game_mean_rating: float,
        generate_prompt: str,
    ):
        if not self.dynamodb_rag_client.check_dynamo_db_key(game_id=game_id):

            game_id_lookup = load_file_local_first(
                path="games", file_name="game_id_lookup.json"
            )
            game_name = game_id_lookup[game_id]
            print(game_name)

            reviews = get_single_game_reviews(
                game_ratings=game_ratings,
                game_id=game_id,
                game_name=game_name,
                sample_pct=0.1,
            )

            weaviate_client.add_reviews_collection_batch(
                collection_name=self.collection_name,
                game_id=game_id,
                reviews=reviews,
            )
            current_prompt = prompt_replacement(
                current_prompt=generate_prompt,
                overall_stats=self.overall_stats,
                game_name=game_name,
                game_mean=str(game_mean_rating),
            )

            summary = weaviate_client.generate_aggregated_review(
                game_id=game_id,
                collection_name=self.collection_name,
                generate_prompt=current_prompt,
            )
            self.dynamodb_rag_client.divide_and_process_generated_summary(
                game_id, summary=summary.generated
            )

            # weaviate_client.remove_collection_items(
            #     game_id=game_id, collection_name=self.collection_name, reviews=reviews
            # )
            return

        print(f"Game {game_id} already processed")

    def rag_description_generation_chain(self):

        self.get_overall_stats()
        game_ids = self.get_game_ids()
        generate_prompt = self.load_prompt()

        weaviate_client = WeaviateClient(ec2=True)
        weaviate_client.create_reviews_collection(collection_name=self.collection_name)

        self.dynamodb_rag_client = RagDynamoDB()

        for game_id in game_ids:
            print(
                f"\nProcessing game {game_id}\n{self.num_completed_games} of {self.end_block}"
            )

            game_mean_rating, game_ratings = self.create_single_game_data(game_id)

            self.process_single_game(
                weaviate_client,
                game_id,
                game_ratings,
                game_mean_rating,
                generate_prompt,
            )

            if ENVIRONMENT != "prod":
                break

            self.num_completed_games += 1

        weaviate_client.close_client()


if __name__ == "__main__":

    start_block = sys.argv[1]
    end_block = sys.argv[2]

    rag_description = RagDescription(start_block=start_block, end_block=end_block)
    rag_description.rag_description_generation_chain()
