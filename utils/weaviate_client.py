import os
import pandas as pd
import weaviate
import weaviate.classes as wvc
from pydantic import BaseModel, ConfigDict
from weaviate.classes.config import Configure
from weaviate.classes.query import Filter, MetadataQuery
from weaviate.util import generate_uuid5

IS_LOCAL = True if os.environ.get("IS_LOCAL", "True").lower() == "true" else False


class WeaviateClient(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    # ip_address: str
    collection_name: str = "None"
    weaviate_client: weaviate.client = None
    collection: weaviate.collections.Collection = None

    def model_post_init(self, __context):
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

    # def connect_weaviate_client_ec2(self) -> weaviate.client:
    #     return weaviate.connect_to_custom(
    #         http_host=self.ip_address,
    #         http_port=8080,
    #         http_secure=False,
    #         grpc_host=self.ip_address,
    #         grpc_port=50051,
    #         grpc_secure=False,
    #         skip_init_checks=False,
    #         headers={
    #             "X-OpenAI-Api-Key": os.environ["OPENAI_API_KEY"],
    #         },
    #     )

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

    def find_near_objects(self, collection_name, uuid, limit: int = 20):
        self.collection = self.weaviate_client.collections.get(collection_name)
        response = self.collection.query.near_object(
            near_object=uuid,
            limit=limit,
            return_metadata=MetadataQuery(distance=True),
        )
        return response.objects

    def add_bgg_collection_batch(
        self,
        df: pd.DataFrame,
        collection_name: str,
        use_about=True,
        attributes: list = [],
    ) -> None:

        self.collection = self.weaviate_client.collections.get(collection_name)
        uuids = []

        with self.collection.batch.dynamic() as batch:

            for index, item in df.iterrows():

                game_object = {
                    "bggid": str(item["bggid"]),
                    "name": str(item["name"]).lower(),
                }
                if use_about:
                    game_object.update({"about": str(item["about"]).lower()})
                if len(attributes):
                    game_object.update({x: float(item[x]) for x in attributes})

                uuid = generate_uuid5(game_object)
                uuids.append(uuid)

                if self.collection.data.exists(uuid):
                    continue
                else:
                    batch.add_object(properties=game_object, uuid=uuid)

        df["UUID"] = uuids
        return df

    def add_reviews_collection_batch(
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

    def create_rag_collection(self):

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
                    skip_vectorization=True,
                    vectorize_property_name=False,
                ),
                wvc.config.Property(
                    name="product_id",
                    data_type=wvc.config.DataType.TEXT,
                    skip_vectorization=True,
                    vectorize_property_name=False,
                ),
            ],
        )

    def create_bgg_collection(
        self, collection_name: str, reset=True, use_about=True, attributes: list = []
    ) -> None:

        if self.weaviate_client.collections.exists(collection_name):
            print("Collection already exists for this block")
            if reset:
                self.weaviate_client.collections.delete(collection_name)
                print("Deleted and recreating collection")
            return

        build_properties = [
            wvc.config.Property(
                name="bggid",
                data_type=wvc.config.DataType.TEXT,
                skip_vectorization=True,
                vectorize_property_name=False,
            ),
            wvc.config.Property(
                name="name",
                data_type=wvc.config.DataType.TEXT,
                skip_vectorization=True,
                vectorize_property_name=False,
            ),
        ]
        if use_about:
            build_properties.append(
                wvc.config.Property(name="about", data_type=wvc.config.DataType.TEXT)
            )
        if len(attributes):
            build_properties += [
                wvc.config.Property(
                    name=x,
                    data_type=wvc.config.DataType.NUMBER,
                    vectorize_property_name=False,
                    skip_vectorization=True,
                )
                for x in attributes
            ]

        self.weaviate_client.collections.create(
            name=collection_name,
            vectorizer_config=[
                Configure.NamedVectors.text2vec_transformers(
                    name="title_vector",
                    source_properties=["title"],
                )
            ],
            properties=build_properties,
        )

    def close_client(self):
        self.weaviate_client.close()
