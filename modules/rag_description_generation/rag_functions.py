import os

# # visualization packages
import pandas as pd
import boto3
import weaviate

# import ruptures as rpt
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from weaviate.classes.query import Filter
from weaviate.util import generate_uuid5

from pydantic import BaseModel


class DynamoDB(BaseModel):
    dynamodb_client: boto3.client = boto3.client("dynamodb")


def filter_stopwords(text: str) -> str:
    stop_words = set(stopwords.words("english"))
    word_tokens = word_tokenize(text)
    filtered_sentence = [w for w in word_tokens if not w.lower() in stop_words]
    return " ".join(filtered_sentence)


def evaluate_quality_words_over_thresh(text: str) -> str:
    word_tokens = word_tokenize(text)
    return len(word_tokens) > 5


def divide_and_process_generated_summary(game_id, summary):
    summary = summary.replace("**", "")
    description = summary.split("\n\n### Pros\n")[0].replace(
        "### What is this game about?\n", ""
    )
    pros = (
        summary.split("\n\n### Pros\n")[1]
        .split("\n\n### Cons\n")[0]
        .replace("\n", "")
        .replace("-", "")
    )
    cons = summary.split("\n\n### Cons\n")[-1].replace("\n", "").replace("-", "")

    response = dynamodb_client.put_item(
        TableName="game_generated_descriptions",
        Item={
            "game_id": {"S": game_id},
            "generated_description": {"S": description},
            "generated_pros": {"S": pros},
            "generated_cons": {"S": cons},
        },
        ConditionExpression="attribute_not_exists(game_id)",
    )
    print(response)


def check_dynamo_db_key(game_id):
    try:
        dynamodb_client.get_item(
            TableName="game_generated_descriptions", Key={"game_id": {"S": game_id}}
        )["Item"]
        print(f"Game {game_id} already exists in DynamoDB")
        return True
    except:
        return False


def add_collection_batch(
    client: weaviate.client, collection_name: str, game_id: str, reviews: list[str]
) -> None:
    collection = client.collections.get(collection_name)
    print(f"Adding reviews for game {game_id}")

    with collection.batch.dynamic() as batch:
        for review in reviews:
            review_item = {
                "review_text": review,
                "product_id": game_id,
            }
            uuid = generate_uuid5(review_item)

            if collection.data.exists(uuid):
                continue
                # if it already exists, update the properties
                collection.data.update(properties=review_item, uuid=uuid)
            else:
                batch.add_object(properties=review_item, uuid=uuid)


def remove_collection_batch(
    client: weaviate.client, collection_name: str, game_id: str, reviews: list[str]
) -> None:
    collection = client.collections.get(collection_name)
    print(f"Removing embeddings for game {game_id}")

    with collection.batch.dynamic() as batch:
        for review in reviews:
            review_item = {
                "review_text": review,
                "product_id": game_id,
            }
            uuid = generate_uuid5(review_item)

            if collection.data.exists(uuid):
                collection.data.delete(uuid=uuid)


def generate_aggregated_review(
    client: weaviate.client, collection_name: str, game_id: str, generate_prompt: str
) -> str:
    print(f"Generating aggregated review for game {game_id}")
    collection = client.collections.get(collection_name)
    summary = collection.generate.near_text(
        query="aggregate_review",
        return_properties=["review_text", "product_id"],
        filters=Filter.by_property("product_id").equal(game_id),
        grouped_task=generate_prompt,
    )
    return summary


def refine_df_for_specific_game(
    df: pd.DataFrame, game_id: str, sample_pct: float = 0.1
) -> pd.DataFrame:

    # immediately filter to only the game_id we're interested in
    df = df[df["BGGId"] == game_id]
    df = df.reset_index(drop=True)
    game_name = df["Name"].iloc[0]

    print(f"\n\nBuilding review data frame for game {game_name}: {game_id}")

    # get the ratings sample distribution by taking 10% of the total ratings
    df["rounded_rating"] = df["rating"].round(0).astype(int)
    sample_size = int(len(df) * sample_pct)  # Desired total sample size
    group_sizes = round(
        df["rounded_rating"].value_counts(normalize=True) * sample_size, 0
    ).astype(int)
    print(f"Desired sample size: {sample_size}")

    # refine to only ratings with comments and clean all comments
    df = df[df["value"].notna()]
    count_reviews_all_comments = len(df)
    print(f"Total reviews with comments: {count_reviews_all_comments}")
    df["value"] = df["value"].replace(r"[^A-Za-z0-9 ]+", "", regex=True)
    df["value"] = df["value"].str.lower().apply(lambda x: filter_stopwords(x))

    df["quality_review"] = df["value"].apply(evaluate_quality_words_over_thresh)
    df = df[df["quality_review"] == True]
    removed_reviews = count_reviews_all_comments - len(df)
    print(
        f"Total quality reviews: {len(df)}. {removed_reviews} reviews removed due to quality threshold"
    )

    if len(df) < sample_size:
        print("Not enough quality reviews to sample from; using all reviews")
    else:
        print(f"Stratified sampling to {sample_size} reviews")
        rating_counts = df["rounded_rating"].value_counts()
        # Ensure we don't sample more than the available values in each group
        adjusted_group_sizes = group_sizes.clip(upper=rating_counts)
        df = df.groupby("rounded_rating", group_keys=False).apply(
            lambda x: x.sample(n=int(adjusted_group_sizes[x.name]), random_state=42)
        )

    # remove all special characters from combined_review
    df["combined_review"] = df["rating"].astype("string") + " " + df["value"]
    df["combined_review"] = df["combined_review"].astype("string")

    avg_rating = round(df["AvgRating"].iloc[0], 1)
    df = df[["BGGId", "Description", "combined_review"]]

    return df, game_name, avg_rating
