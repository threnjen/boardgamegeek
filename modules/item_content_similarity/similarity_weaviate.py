import os

import weaviate
import weaviate.classes as wvc
from pydantic import BaseModel, ConfigDict
from weaviate.classes.config import Configure
from weaviate.classes.query import Filter
from weaviate.classes.query import MetadataQuery
from weaviate.util import generate_uuid5

IS_LOCAL = True if os.environ.get("IS_LOCAL", "True").lower() == "true" else False


class WeaviateClient(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    # ip_address: str
    collection_name: str = "None"
    weaviate_client: weaviate.client = None
    collection: weaviate.collections.Collection = None

    def model_post_init(self, __context):
        # self.weaviate_client = self.connect_weaviate_client_ec2()
        self.weaviate_client = self.connect_weaviate_client_docker()

    def connect_weaviate_client_docker(self) -> weaviate.client:
        if not IS_LOCAL:
            client = weaviate.connect_to_local(
                host="127.0.0.1",
                port=8081,
                grpc_port=50051,
                headers={
                    "X-OpenAI-Api-Key": os.environ["OPENAI_API_KEY"],
                },
            )
            return client

        return weaviate.connect_to_local(
            port=8081,
            headers={
                "X-OpenAI-Api-Key": os.environ["OPENAI_API_KEY"],
            },
        )

    def close_client(self):
        self.weaviate_client.close()

    def add_collection_item(self, item) -> None:

        self.collection = self.weaviate_client.collections.get(self.collection_name)

        print(f"Adding data for game {item["BGGId"]}")

        game_object = {
            "bggid": str(item["BGGId"]),
            "description": str(item["Description"]).lower(),
            "about": str(item["About"]).lower(),
            "positive": str(item["Positive"]).lower(),
            "negative": str(item["Negative"]).lower(),
        }

        uuid = self.collection.data.insert(properties=game_object)
        return uuid

    def find_near_objects(self, uuid):
        self.collection = self.weaviate_client.collections.get(self.collection_name)
        response = self.collection.query.near_object(
            near_object=uuid,
            limit=20,
            return_metadata=MetadataQuery(distance=True),
        )
        return response.objects

    def create_rag_collection(self):

        if self.weaviate_client.collections.exists(self.collection_name):
            print("Collection already exists for this block")
            self.weaviate_client.collections.delete(self.collection_name)
            return

        self.weaviate_client.collections.create(
            name=self.collection_name,
            vectorizer_config=[
                Configure.NamedVectors.text2vec_transformers(
                    name="title_vector",
                    source_properties=["title"],
                )
            ],
            # generative_config=wvc.config.Configure.Generative.openai(
            #     model="gpt-4o-mini"
            # ),
            properties=[
                wvc.config.Property(
                    name="bggid",
                    data_type=wvc.config.DataType.TEXT,
                    skip_vectorization=True,
                    vectorize_property_name=False,
                ),
                wvc.config.Property(
                    name="description", data_type=wvc.config.DataType.TEXT
                ),
                wvc.config.Property(name="about", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(
                    name="positive", data_type=wvc.config.DataType.TEXT
                ),
                wvc.config.Property(
                    name="negative", data_type=wvc.config.DataType.TEXT
                ),
            ],
        )

    def close_client(self):
        self.weaviate_client.close()

    # def remove_collection_items(
    #     self,
    #     game_id: str,
    #     reviews: list[str],
    # ) -> None:

    #     print(f"Removing embeddings for game {game_id}")

    #     for review in reviews:
    #         review_item = {
    #             "review_text": review,
    #             "product_id": game_id,
    #         }
    #         uuid = generate_uuid5(review_item)

    #         if self.collection.data.exists(uuid):
    #             self.collection.data.delete_by_id(uuid=uuid)

    # def generate_aggregated_review(
    #     self,
    #     game_id: str,
    #     generate_prompt: str,
    # ) -> str:
    #     print(f"Generating aggregated review for game {game_id}")

    #     summary = self.collection.generate.near_text(
    #         query="aggregate_review",
    #         return_properties=["review_text", "product_id"],
    #         filters=Filter.by_property("product_id").equal(game_id),
    #         grouped_task=generate_prompt,
    #     )
    #     return summary

    # def add_reviews_collection_batch(
    #     self,
    #     game_id: str,
    #     reviews: list[str],
    # ) -> None:

    #     print(f"Adding reviews for game {game_id}")

    #     with self.collection.batch.dynamic() as batch:
    #         for review in reviews:
    #             review_item = {
    #                 "review_text": review,
    #                 "product_id": game_id,
    #             }
    #             uuid = generate_uuid5(review_item)

    #             if self.collection.data.exists(uuid):
    #                 continue
    #             else:
    #                 batch.add_object(properties=review_item, uuid=uuid)

    #     print(f"Reviews added for game {game_id}")
