import gc
import json
import os
import sys

import pandas as pd
from config import CONFIGS
from modules.rag_description_generation.ec2_weaviate import Ec2
from modules.rag_description_generation.rag_dynamodb import DynamoDB
from modules.rag_description_generation.rag_functions import get_single_game_entries
from modules.rag_description_generation.rag_weaviate import WeaviateClient
from pydantic import BaseModel, ConfigDict
from utils.processing_functions import load_file_local_first

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
S3_SCRAPER_BUCKET = CONFIGS["s3_scraper_bucket"]
GAME_CONFIGS = CONFIGS["games"]
USER_CONFIGS = CONFIGS["users"]
IS_LOCAL = True if os.environ.get("IS_LOCAL", "False").lower() == "true" else False


class RagDescription(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    start_block: str
    end_block: str
    ip_address: str = None
    overall_stats: dict = {}
    game_ids: list = []
    generate_prompt: str = None
    weaviate: WeaviateClient = None
    dynamodb_client: DynamoDB = None

    def model_post_init(self, __context):
        self.start_block = int(self.start_block)
        self.end_block = int(self.end_block)

    def confirm_running_ec2_host(self):
        ec2_instance = Ec2()
        ec2_instance.validate_ready_weaviate_instance()
        self.ip_address = ec2_instance.get_ip_address()
        ec2_instance.copy_docker_compose_to_instance()
        ec2_instance.start_docker()

    def stop_ec2_instance(self):
        ec2_instance = Ec2()
        self.ip_address = ec2_instance.get_ip_address()
        ec2_instance.stop_instance()

    def compute_game_overall_stats(self, game_df):
        overall_mean = round(game_df["AvgRating"].describe()["mean"], 2)
        game_std = round(game_df["AvgRating"].describe()["std"], 2)

        self.overall_stats["overall_mean"] = overall_mean
        self.overall_stats["overall_std"] = game_std
        self.overall_stats["two_under"] = round(overall_mean - 2 * game_std, 2)
        self.overall_stats["one_under"] = round(overall_mean - game_std, 2)
        self.overall_stats["half_over"] = round(overall_mean + 0.5 * game_std, 2)
        self.overall_stats["one_over"] = round(overall_mean + game_std, 2)

        print(f"Overall mean: {overall_mean}")

    def load_reduced_game_df(self):
        print(f"\nLoading game data from {GAME_CONFIGS['clean_dfs_directory']}")
        game_df = load_file_local_first(
            path=GAME_CONFIGS["clean_dfs_directory"], file_name="games_clean.pkl"
        )

        self.compute_game_overall_stats(game_df)

        game_df_reduced = game_df.sort_values("BayesAvgRating", ascending=False)[
            self.start_block : self.end_block
        ]

        self.game_ids = game_df_reduced["BGGId"].astype(str).tolist()

        if ENVIRONMENT != "prod":
            self.game_ids = self.game_ids[:2]
            game_df_reduced = game_df_reduced.head(2)

        del game_df
        gc.collect()

        return game_df_reduced

    def merge_game_df_with_user_df(self, game_df_reduced):
        print(f"\nLoading user ratings from {USER_CONFIGS['clean_dfs_directory']}")
        user_df = load_file_local_first(
            path=USER_CONFIGS["clean_dfs_directory"],
            file_name="complete_user_ratings.pkl",
        )

        print(
            f"Reducing user ratings to only include games in the reduced game dataframe\n"
        )
        all_games_df = user_df.merge(
            game_df_reduced[
                ["BGGId", "Name", "Description", "AvgRating", "BayesAvgRating"]
            ],
            on="BGGId",
            how="inner",
        )
        all_games_df["BGGId"] = all_games_df["BGGId"].astype("string")
        del game_df_reduced
        del user_df
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
                df=all_games_df, game_id=game_id, sample_pct=0.05
            )
            reviews = df["combined_review"].to_list()
            weaviate_client.add_collection_batch(game_id=game_id, reviews=reviews)
            current_prompt = weaviate_client.prompt_replacement(
                current_prompt=generate_prompt,
                overall_stats=self.overall_stats,
                game_name=game_name,
                game_mean=game_mean,
            )
            print(current_prompt)
            summary = weaviate_client.generate_aggregated_review(
                game_id, current_prompt
            )
            self.dynamodb_client.divide_and_process_generated_summary(
                game_id, summary=summary.generated
            )
            print(f"\n{summary.generated}")
            weaviate_client.remove_collection_items(game_id=game_id, reviews=reviews)
            return

        print(f"Game {game_id} already processed")

    def rag_description_generation_chain(self):
        self.confirm_running_ec2_host()
        game_df_reduced = self.load_reduced_game_df()
        all_games_df = self.merge_game_df_with_user_df(game_df_reduced)
        generate_prompt = self.load_prompt()

        weaviate_client = WeaviateClient(
            ip_address=self.ip_address,
            collection_name=f"reviews_{self.start_block}_{self.end_block}",
        )
        weaviate_client.create_weaviate_collection()

        self.dynamodb_client = DynamoDB()

        for game_id in self.game_ids:
            print(f"\nProcessing game {game_id}")
            self.process_single_game(
                weaviate_client, game_id, all_games_df, generate_prompt
            )

        weaviate_client.close_client()


if __name__ == "__main__":

    start_block = sys.argv[1]
    end_block = sys.argv[2]

    print(start_block, end_block)

    rag_description = RagDescription(start_block=start_block, end_block=end_block)
    rag_description.rag_description_generation_chain()
