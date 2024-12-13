import os

import weaviate
import weaviate.classes as wvc
from pydantic import BaseModel, ConfigDict
from weaviate.classes.config import Configure
from weaviate.classes.query import Filter
from weaviate.util import generate_uuid5


class WeaviateClient(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    ip_address: str
    collection_name: str
    weaviate_client: weaviate.client = None
    collection: weaviate.collections.Collection = None

    def model_post_init(self, __context):
        self.weaviate_client = self.connect_weaviate_client_ec2()
        self.collection = self.weaviate_client.collections.get(self.collection_name)

    def connect_weaviate_client_ec2(self) -> weaviate.client:
        return weaviate.connect_to_custom(
            http_host=self.ip_address,
            http_port=8080,
            http_secure=False,
            grpc_host=self.ip_address,
            grpc_port=50051,
            grpc_secure=False,
            skip_init_checks=False,
            headers={
                "X-OpenAI-Api-Key": os.environ["OPENAI_API_KEY"],
            },
        )

    def prompt_replacement(
        self,
        current_prompt: str,
        overall_stats: dict[float],
        game_name: str,
        game_mean: str,
    ) -> str:

        # turn all stats to strings
        overall_stats = {k: str(v) for k, v in overall_stats.items()}

        current_prompt = current_prompt.replace("{GAME_NAME_HERE}", game_name)
        current_prompt = current_prompt.replace("{GAME_AVERAGE_HERE}", game_mean)
        current_prompt = current_prompt.replace(
            "{TWO_UNDER}", overall_stats["two_under"]
        )
        current_prompt = current_prompt.replace(
            "{ONE_UNDER}", overall_stats["one_under"]
        )
        current_prompt = current_prompt.replace("{ONE_OVER}", overall_stats["one_over"])
        current_prompt = current_prompt.replace(
            "{HALF_OVER}", overall_stats["half_over"]
        )
        current_prompt = current_prompt.replace(
            "{OVERALL_MEAN}", overall_stats["overall_mean"]
        )
        return current_prompt

    def add_collection_batch(
        self,
        game_id: str,
        reviews: list[str],
    ) -> None:

        print(f"Adding reviews for game {game_id}")

        with self.collection.batch.dynamic() as batch:
            for review in reviews:
                review_item = {
                    "review_text": review,
                    "product_id": game_id,
                }
                uuid = generate_uuid5(review_item)

                if self.collection.data.exists(uuid):
                    continue
                else:
                    batch.add_object(properties=review_item, uuid=uuid)

        print(f"Reviews added for game {game_id}")

    def remove_collection_items(
        self,
        game_id: str,
        reviews: list[str],
    ) -> None:

        print(f"Removing embeddings for game {game_id}")

        for review in reviews:
            review_item = {
                "review_text": review,
                "product_id": game_id,
            }
            uuid = generate_uuid5(review_item)

            if self.collection.data.exists(uuid):
                self.collection.data.delete_by_id(uuid=uuid)

    def generate_aggregated_review(
        self,
        game_id: str,
        generate_prompt: str,
    ) -> str:
        print(f"Generating aggregated review for game {game_id}")

        summary = self.collection.generate.near_text(
            query="aggregate_review",
            return_properties=["review_text", "product_id"],
            filters=Filter.by_property("product_id").equal(game_id),
            grouped_task=generate_prompt,
        )
        return summary

    def create_weaviate_collection(self):

        if self.weaviate_client.collections.exists(self.collection_name):
            print("Collection already exists for this block")
            return

        self.weaviate_client.collections.create(
            name=self.collection_name,
            vectorizer_config=[
                Configure.NamedVectors.text2vec_transformers(
                    name="title_vector",
                    source_properties=["title"],
                )
            ],
            generative_config=wvc.config.Configure.Generative.openai(
                model="gpt-4o-mini"
            ),
            properties=[
                wvc.config.Property(
                    name="review_text",
                    data_type=wvc.config.DataType.TEXT,
                ),
                wvc.config.Property(
                    name="product_id",
                    data_type=wvc.config.DataType.TEXT,
                    skip_vectorization=True,
                    vectorize_property_name=False,
                ),
            ],
        )

    def close_client(self):
        self.weaviate_client.close()


def connect_weaviate_client_docker() -> weaviate.client:
    client = weaviate.connect_to_local(
        headers={
            # "X-HuggingFace-Api-Key": os.environ["HUGGINGFACE_APIKEY"],
            "X-OpenAI-Api-Key": os.environ["OPENAI_API_KEY"],
        }
    )
    return client
