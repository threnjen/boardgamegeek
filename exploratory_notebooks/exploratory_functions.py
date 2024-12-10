import gc
import json
import os
import time
from datetime import datetime
from typing import Tuple

# # visualization packages
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import regex as re
import requests
import boto3
import seaborn as sns
import weaviate
import weaviate.classes as wvc
from weaviate.embedded import EmbeddedOptions

# import ruptures as rpt
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sentence_transformers import SentenceTransformer
from weaviate.classes.config import Configure
from weaviate.classes.query import Filter
from weaviate.util import generate_uuid5

dynamodb_client = boto3.client("dynamodb", region_name="us-west-2")


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


def connect_weaviate_client_local() -> weaviate.client:
    client = weaviate.WeaviateClient(
        additional_headers={
            "X-HuggingFace-Api-Key": os.environ["HUGGINGFACE_APIKEY"],
            "X-OpenAI-Api-Key": os.environ["OPENAI_API_KEY"],
        },
        embedded_options=EmbeddedOptions(
            additional_env_vars={
                "ENABLE_MODULES": "backup-filesystem,text2vec-openai,text2vec-cohere,text2vec-huggingface,ref2vec-centroid,generative-openai,qna-openai",
                "BACKUP_FILESYSTEM_PATH": "/tmp/backups",
            }
        ),
    )

    return client


def connect_weaviate_client_docker() -> weaviate.client:
    client = weaviate.connect_to_local(
        headers={
            # "X-HuggingFace-Api-Key": os.environ["HUGGINGFACE_APIKEY"],
            "X-OpenAI-Api-Key": os.environ["OPENAI_API_KEY"],
        }
    )
    return client


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


def get_negative_trolls(users):
    # get how many ratings each user has
    all_ratings = users.groupby("username")["rating"].count()

    # Get the IQR for ratings across the entire dataset
    within_bounds = get_iqr(users)

    # count how many ratings each user has that are under the IQR lower bound
    under_bounds = (
        users[users["rating"] < within_bounds[0]].groupby("username")["rating"].count()
    )

    # get the difference between all_ratings and under_bounds
    ratings_diffs = pd.DataFrame(all_ratings - under_bounds)

    # get the usernames of the users who have all ratings under the bounds and call these troll_raters
    negative_troll_raters = ratings_diffs[ratings_diffs["rating"] == 0].index

    print(f"Number of negative troll raters: {len(negative_troll_raters)}")

    # get the users who are trolls
    negative_troll_users = users[users["username"].isin(negative_troll_raters)]

    return negative_troll_users


def get_positive_trolls(users):
    # get how many ratings each user has
    all_ratings = users.groupby("username")["rating"].count()

    # count how many ratings each user has that are 10s
    all_10s = users[users["rating"] == 10].groupby("username")["rating"].count()

    # get the difference between the two
    ratings_diffs = pd.DataFrame(all_ratings - all_10s)

    # get the usernames of the users who have all 10 ratings and call these potential happy trolls
    potential_happy_trolls = ratings_diffs[ratings_diffs["rating"] == 0].index

    # get the users who are potential trolls
    potential_happy_troll_users = users[users["username"].isin(potential_happy_trolls)]

    print(f"Number of potential happy troll raters: {len(potential_happy_trolls)}")

    return potential_happy_troll_users


def get_extreme_rating_trolls(users):
    # get how many ratings each user has
    all_ratings = users.groupby("username")["rating"].count()

    # Get the IQR for ratings across the entire dataset
    within_bounds = get_iqr(users)

    not_within_bounds = (
        users[~users["rating"].between(within_bounds[0], 9.5)]
        .groupby("username")["rating"]
        .count()
    )

    # get the difference between the two
    ratings_diffs = pd.DataFrame(all_ratings - not_within_bounds)

    # get the usernames of the users who have all 10 ratings and call these potential happy trolls
    potential_extreme_trolls = ratings_diffs[ratings_diffs["rating"] == 0].index

    # get the users who are potential trolls
    potential_extreme_users = users[users["username"].isin(potential_extreme_trolls)]

    return potential_extreme_users


def clear_general_trolls(users):

    negative_troll_users = get_negative_trolls(users)

    # get the users who are not trolls and write back to users
    users = users[~users["username"].isin(negative_troll_users["username"])]

    potential_happy_troll_users = get_positive_trolls(users)

    potential_extreme_users = get_extreme_rating_trolls(users)
    potential_extreme_users = potential_extreme_users[
        ~potential_extreme_users["username"].isin(
            potential_happy_troll_users["username"]
        )
    ]
    print(
        f"Number of potential extreme troll raters: {len(potential_extreme_users['username'].unique())}"
    )

    # get the users who are not trolls and write back to users
    users = users[~users["username"].isin(potential_extreme_users["username"])]

    return (
        users,
        negative_troll_users,
        potential_happy_troll_users,
        potential_extreme_users,
    )


def get_subset(
    games: pd.DataFrame, users: pd.DataFrame, mechanics: pd.DataFrame, game_id: int
) -> Tuple[pd.DataFrame]:
    game = games[games["BGGId"] == game_id]
    users_game = users[users["BGGId"] == game_id]

    users_game["lastmodified"] = pd.to_datetime(users_game["lastmodified"])

    # Create 'day' column with only year, month, day
    users_game["dayrated"] = users_game["lastmodified"].dt.floor("D")

    # Create 'month' column with year and month only
    users_game["monthrated"] = pd.to_datetime(
        users_game["lastmodified"].dt.to_period("M").astype(str)
    )

    users_game["lastmodified"] = users_game["lastmodified"].dt.date
    users_game["rating"] = users_game["rating"].round(1)

    mechanics_game = mechanics[mechanics["BGGId"] == game_id]
    # Step 1: Create dummy variables for each mechanic
    dummies = pd.get_dummies(mechanics_game["mechanic"])

    # Step 2: Add the BGGId and group by it
    mechanics_game = (
        mechanics_game[["BGGId"]]
        .join(dummies)
        .groupby("BGGId")
        .max()
        .astype(int)
        .reset_index()
    )

    this_game = game.merge(
        mechanics_game, left_on="BGGId", right_on="BGGId", how="left"
    ).reset_index(drop=True)

    rated_date_distribution = (
        users_game.groupby(users_game["monthrated"])["rating"].count().reset_index()
    )

    return this_game, users_game, mechanics_game, rated_date_distribution


def plot_ratings_dist(game_ratings_dist_df_df):
    # Visualize to detect the jump
    plt.figure(figsize=(10, 6))
    plt.plot(
        game_ratings_dist_df_df["monthrated"],
        game_ratings_dist_df_df["rating"],
        marker="o",
        linestyle="-",
        color="blue",
    )
    plt.title("Count of Ratings Over Time", fontsize=16)
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Rating Count", fontsize=12)
    plt.grid(True)
    plt.show()


def get_iqr(df, thresh=1.5):

    ratings_count_mean = int(round(df["rating"].mean(), 0))
    # ratings_count_median = int(round(df["rating"].median(), 0))
    # std_dev = int(round(df["rating"].std(), 0))

    # print(
    #     f"Mean: {ratings_count_mean}, Median: {ratings_count_median}, Std dev: {std_dev}"
    # )

    q1 = df["rating"].quantile(0.25)
    q3 = df["rating"].quantile(0.75)

    iqr = q3 - q1

    iqr_15 = iqr * thresh

    within_bounds = (ratings_count_mean - iqr_15, ratings_count_mean + iqr_15)
    # print(f"IQR: {iqr}, Boundaries: {within_bounds}")

    # show me the review dates where the rating is outside the within_bounds
    return within_bounds


def identify_bomb_events(users_df, release_date):
    users_game = users_df[users_df["monthrated"] >= release_date]

    users_game["dayrated"] = pd.to_datetime(
        users_game["dayrated"]
    )  # Ensure 'dayrated' is in datetime format

    df_all_review_counts = (
        users_game.groupby("dayrated")["rating"]
        .count()
        .reset_index()
        .rename(columns={"rating": "total_review_count"})
    )
    df_all_review_counts["rolling_count_avg"] = (
        df_all_review_counts["total_review_count"]
        .rolling(window=14, center=False, min_periods=1)
        .mean()
        .round(2)
    )

    df_extreme = (
        users_game[users_game["rating"].isin([1, 2, 3, 10])]
        .groupby("dayrated")["rating"]
        .count()
        .reset_index()
        .rename(columns={"rating": "ext_count"})
    )
    df_extreme["rolling_ext_count"] = (
        df_extreme["ext_count"]
        .rolling(window=14, center=False, min_periods=1)
        .mean()
        .round(2)
    )

    df_review_counts = pd.merge(
        df_all_review_counts, df_extreme, on="dayrated", how="left"
    )

    df_review_counts["ext_count"] = df_review_counts["ext_count"].fillna(0).astype(int)
    df_review_counts["rolling_ext_count"] = df_review_counts[
        "rolling_ext_count"
    ].fillna(0)

    df_review_counts["pct_extreme"] = (
        df_review_counts["ext_count"] / df_review_counts["total_review_count"]
    ).round(2)

    # evaluate special review events
    df_review_counts["rating_event"] = df_review_counts["total_review_count"] > (
        df_review_counts["rolling_count_avg"] * 2
    )
    df_review_counts["bombing_event"] = df_review_counts["ext_count"] > (
        df_review_counts["rolling_ext_count"] * 2
    )
    general_extreme_ratio = (
        df_review_counts["ext_count"].sum()
        / df_review_counts["total_review_count"].sum()
    )
    df_review_counts["ratio_event"] = (
        df_review_counts["ext_count"] / df_review_counts["total_review_count"]
        > general_extreme_ratio
    )

    combined_event = df_review_counts[
        (df_review_counts["rating_event"])
        & (df_review_counts["bombing_event"])
        & (df_review_counts["ratio_event"])
    ]
    event_indices = combined_event["dayrated"].to_list()
    return users_df[
        (users_df["dayrated"].isin(event_indices))
        & (users_df["rating"].isin([1, 2, 3, 10]))
        & (users_df["value"].notna())
    ]


def find_potential_trolls(users_df, game_ratings_dist_df):

    # get the IQR for the ratings distribution
    within_bounds = get_iqr(users_df, thresh=3)
    # get the release date and spike indices
    release_date_index, abnormal_spike_months_indices = estimate_spike_indices(
        game_ratings_dist_df
    )
    release_date = game_ratings_dist_df.iloc[release_date_index]["monthrated"]

    # build the data frames for potential low scoring trolls below the IQR lower bound
    potential_troll_negatives_df = users_df[
        (users_df["rating"] < within_bounds[0]) & users_df["value"].notna()
    ]
    potential_troll_negatives_df["flag_reason"] = "Below IQR lower bound with comments"

    # build the data frame for users who rated before the release date and left no comments
    before_release_date_df_no_comments = users_df[
        (users_df["monthrated"] < release_date) & (users_df["value"].isna())
    ]
    before_release_date_df_no_comments["flag_reason"] = (
        "Before release date, no comments"
    )

    # build the data frame for users who rated before the release date and left comments
    before_release_date_df_comments = users_df[
        (users_df["monthrated"] < release_date) & (users_df["value"].notna())
    ]
    before_release_date_df_comments["flag_reason"] = (
        "Before release date, with comments"
    )

    # build suspicious ratings days based on review bomb events
    suspicious_events_df = identify_bomb_events(users_df, release_date)
    suspicious_events_df["flag_reason"] = "Rating occured on a rating event day"

    # build the data frames for potential 10-scoring trolls
    potential_troll_positives_df = users_df[
        (users_df["rating"] == 10) & users_df["value"].notna()
    ]
    potential_troll_positives_df["flag_reason"] = "All 10s with comments"

    print(
        f"Game stats:\n\
        Rating occured on a rating event day: {len(suspicious_events_df)}\n\
          Below IQR lower bound with comments: {len(potential_troll_negatives_df)}\n\
            Before release date, no comments: {len(before_release_date_df_no_comments)}\n\
            Before release date, with comments: {len(before_release_date_df_comments)}\n\
            All 10s with comments: {len(potential_troll_positives_df)}\n"
    )

    aggregated_df = pd.concat(
        [
            suspicious_events_df,
            potential_troll_negatives_df,
            before_release_date_df_no_comments,
            before_release_date_df_comments,
            potential_troll_positives_df,
        ]
    )
    aggregated_df = aggregated_df.drop_duplicates(subset=["username"], keep="first")
    print(aggregated_df["flag_reason"].value_counts())

    return aggregated_df


# def estimate_game_release_date(game_ratings_dist_df, window=3, center=False):
#     """Identify release date using ruptures package"""
#     print("Nonsense")

#     game_ratings_dist_df["rolling_ratings"] = (
#         game_ratings_dist_df["rating"]
#         .rolling(window=window, center=center, min_periods=1)
#         .mean()
#         .round(2)
#     )

#     ratings_series = (
#         game_ratings_dist_df["rolling_ratings"].fillna(0).to_numpy()
#     )

#     # Binary Segmentation search method is l2

#     algo = rpt.Pelt(model="rbf").fit(
#         ratings_series
#     )  # "rbf" works well for nonlinear trends
#     change_points = algo.predict(pen=3)  # Adjust `pen` to control sensitivity
#     print(change_points)

#     # display
#     rpt.display(ratings_series, change_points)
#     plt.show()

#     change_points = [x - 1 for x in change_points]  # Convert to 0-indexed

#     release_date_index = change_points[0]  # The first change point
#     other_spike_points = change_points[1:]  # additional change points

#     release_date = game_ratings_dist_df.iloc[release_date_index][
#         "monthrated"
#     ]  # this is the guessed actual release month for the item
#     print(f"Estimated release date: {release_date}")

#     abnormal_spike_months = game_ratings_dist_df.iloc[other_spike_points][
#         "monthrated"
#     ].to_list()

#     print(f"Potential other spike months to investigate: {abnormal_spike_months}")

#     return release_date, abnormal_spike_months


def estimate_spike_indices(
    game_ratings_dist_df, metric="rating", date_granularity="monthrated"
):
    game_ratings_dist_df = add_ratings_metrics(game_ratings_dist_df, metric=metric)
    explode_points = game_ratings_dist_df[
        game_ratings_dist_df["rolling_expl_pct_change"] > 10000
    ].index

    if not explode_points.any():
        print("No spikes detected")
        initial_spike_date = game_ratings_dist_df.iloc[0][date_granularity]
        print(f"Estimated spike: {initial_spike_date}")
        return 0, []

    initial_spike_date = game_ratings_dist_df.iloc[explode_points[0]][
        date_granularity
    ]  # this is the guessed actual release month for the item
    abnormal_spike_dates = game_ratings_dist_df.iloc[explode_points[1:]][
        date_granularity
    ].to_list()

    print(f"Initial spike date: {initial_spike_date}")
    print(f"Potential other spike dates to investigate: {abnormal_spike_dates}")

    return explode_points[0], explode_points[1:]


def add_ratings_metrics(game_ratings_dist_df, metric="rating"):

    game_ratings_dist_df[f"rolling_{metric}"] = (
        game_ratings_dist_df[metric]
        .rolling(window=3, center=False, min_periods=1)
        .mean()
        .round(2)
    )

    game_ratings_dist_df["rolling_pct_change"] = (
        game_ratings_dist_df[f"rolling_{metric}"].pct_change().round(2)
    ) * 100

    game_ratings_dist_df["exploded"] = game_ratings_dist_df[metric] ** 2
    game_ratings_dist_df["exploded_pct_change"] = (
        game_ratings_dist_df["exploded"].pct_change().round(2)
    ) * 100
    game_ratings_dist_df["rolling_exploded"] = (
        game_ratings_dist_df["exploded"]
        .rolling(window=3, center=False, min_periods=1)
        .mean()
        .round(2)
    )

    game_ratings_dist_df["rolling_expl_pct_change"] = (
        game_ratings_dist_df["rolling_exploded"].pct_change().round(2)
    ) * 100

    return game_ratings_dist_df
