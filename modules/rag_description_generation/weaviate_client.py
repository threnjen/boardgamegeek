import os

import pandas as pd
import weaviate
import weaviate.classes as wvc
from pydantic import BaseModel, ConfigDict

# from weaviate.classes.config import Configure
from weaviate.classes.query import Filter, MetadataQuery
from weaviate.util import generate_uuid5
from modules.rag_description_generation.weaviate_ec2_client import WeaviateEc2

IS_LOCAL = True if os.environ.get("IS_LOCAL", "True").lower() == "true" else False


class WeaviateClient(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    weaviate_client: weaviate.client = None
    ec2: bool = False

    def model_post_init(self, __context):
        self.weaviate_client = self.connect_to_weaviate_client()

    def connect_to_weaviate_client(self):
        if not self.ec2:
            return self.connect_weaviate_client_docker()
        else:
            return self.connect_weaviate_client_ec2()

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
            print("\nConnected to Weaviate instance on Fargate ECS")
            return client

        print("\nConnected to Weaviate instance on local machine")
        return weaviate.connect_to_local(
            port=8081,
            headers={
                "X-OpenAI-Api-Key": os.environ["OPENAI_API_KEY"],
            },
        )

    def connect_weaviate_client_ec2(self) -> weaviate.client:

        weaviate_ec2 = WeaviateEc2()
        weaviate_ec2.validate_ready_weaviate_instance()
        ip_address = weaviate_ec2.get_ip_address()
        weaviate_ec2.start_weaviate_docker_containers()

        print("\nConnected to Weaviate instance on AWS EC2")

        return weaviate.connect_to_custom(
            http_host=ip_address,
            http_port=8080,
            http_secure=False,
            grpc_host=ip_address,
            grpc_port=50051,
            grpc_secure=False,
            skip_init_checks=False,
            headers={
                "X-OpenAI-Api-Key": os.environ["OPENAI_API_KEY"],
            },
        )

    def fetch_single_object(self, collection_name: str, uuid: str):
        collection = self.weaviate_client.collections.get(collection_name)
        return collection.query.fetch_object_by_id(uuid)

    def find_near_objects(self, collection_name, uuid, limit: int = 20):
        collection = self.weaviate_client.collections.get(collection_name)
        response = collection.query.near_object(
            near_object=uuid,
            limit=limit,
            return_metadata=MetadataQuery(distance=True),
        )
        return response.objects

    def check_collection_exists(self, collection_name: str, reset: bool = True) -> bool:
        if self.weaviate_client.collections.exists(collection_name):
            print(f"Collection {collection_name} already exists for this block")
            if reset:
                self.weaviate_client.collections.delete(collection_name)
                print(f"Deleted and recreating collection {collection_name}")
                return False
            return True

    def create_reviews_collection(self, collection_name: str, reset: bool = True):

        if not self.check_collection_exists(collection_name, reset):

            self.weaviate_client.collections.create(
                name=collection_name,
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

    def add_reviews_collection_batch(
        self,
        game_id: str,
        collection_name: str,
        reviews: list[str],
    ) -> None:

        print(f"Adding reviews for game {game_id}")
        collection = self.weaviate_client.collections.get(collection_name)

        with collection.batch.dynamic() as batch:
            for review in reviews:
                review_item = {
                    "review_text": review,
                    "product_id": game_id,
                }
                uuid = generate_uuid5(review_item)

                if collection.data.exists(uuid):
                    continue
                else:
                    batch.add_object(properties=review_item, uuid=uuid)

        print(f"Reviews added for game {game_id}")

    def create_attributes_collection(
        self,
        collection_name: str,
        reset: bool = True,
    ) -> None:

        if not self.check_collection_exists(collection_name, reset):

            self.weaviate_client.collections.create(
                name=collection_name,
                properties=[
                    wvc.config.Property(
                        name="attribute_name",
                        data_type=wvc.config.DataType.TEXT,
                        skip_vectorization=True,
                        vectorize_property_name=False,
                    ),
                    wvc.config.Property(
                        name="attribute",
                        data_type=wvc.config.DataType.TEXT,
                        vectorize_property_name=False,
                    ),
                ],
            )

    def add_attributes_collection_batch(
        self, attributes: list, collection_name: str
    ) -> None:

        collection = self.weaviate_client.collections.get(collection_name)
        attributes_store = {}

        with collection.batch.dynamic() as batch:

            for attribute in attributes:

                print(f"Adding data for attribute {attribute}")

                attribute_object = {
                    "attribute_name": attribute,
                    "attribute": attribute,
                }

                uuid = generate_uuid5(attribute_object)
                attributes_store[attribute] = uuid

                if collection.data.exists(uuid):
                    continue
                else:
                    batch.add_object(properties=attribute_object, uuid=uuid)

        return attributes_store

    def create_bgg_collection(
        self,
        collection_name: str,
        reset: bool = True,
        use_about: bool = False,
        use_description: bool = False,
        attributes: list = [],
    ) -> None:

        if not self.check_collection_exists(collection_name, reset):

            build_properties = [
                wvc.config.Property(
                    name="bggid",
                    data_type=wvc.config.DataType.TEXT,
                    skip_vectorization=True,
                    vectorize_property_name=False,
                )
            ]
            if use_about:
                build_properties.append(
                    wvc.config.Property(
                        name="about", data_type=wvc.config.DataType.TEXT
                    )
                )
            if use_description:
                build_properties.append(
                    wvc.config.Property(
                        name="description", data_type=wvc.config.DataType.TEXT
                    )
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
                properties=build_properties,
            )

    def add_bgg_collection_batch(
        self,
        df: pd.DataFrame,
        collection_name: str,
        use_about=False,
        use_description=False,
        attributes: list = [],
    ) -> None:

        collection = self.weaviate_client.collections.get(collection_name)
        uuids = []

        with collection.batch.dynamic() as batch:

            for index, item in df.iterrows():

                game_object = {
                    "bggid": str(item["bggid"]),
                    # "name": str(item["name"]).lower(),
                }
                if use_about:
                    game_object.update({"about": str(item["about"]).lower()})
                if use_description:
                    game_object.update(
                        {"description": str(item["description"]).lower()}
                    )

                if len(attributes):
                    game_object.update({x: float(item[x]) for x in attributes})

                uuid = generate_uuid5(game_object)
                uuids.append(uuid)

                if collection.data.exists(uuid):
                    continue
                else:
                    batch.add_object(properties=game_object, uuid=uuid)

        df["UUID"] = uuids
        return df

    def remove_collection_items(
        self,
        game_id: str,
        collection_name: str,
        reviews: list[str],
    ) -> None:

        collection = self.weaviate_client.collections.get(collection_name)

        print(f"Removing embeddings for game {game_id}")

        for review in reviews:
            review_item = {
                "review_text": review,
                "product_id": game_id,
            }
            uuid = generate_uuid5(review_item)

            if collection.data.exists(uuid):
                collection.data.delete_by_id(uuid=uuid)

    def generate_aggregated_review(
        self,
        game_id: str,
        collection_name: str,
        generate_prompt: str,
    ) -> str:
        print(f"Generating aggregated review for game {game_id}")

        collection = self.weaviate_client.collections.get(collection_name)

        summary = collection.generate.near_text(
            query="aggregate_review",
            return_properties=["review_text", "product_id"],
            filters=Filter.by_property("product_id").equal(game_id),
            grouped_task=generate_prompt,
        )
        return summary

    def close_client(self):
        self.weaviate_client.close()
