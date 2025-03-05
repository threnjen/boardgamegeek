from typing import Tuple

import pandas as pd

from utils.nlp_functions import evaluate_quality_words_over_thresh, filter_stopwords


def prompt_replacement(
    current_prompt: str,
    overall_stats: dict[float],
    game_name: str,
    game_mean: str,
) -> str:

    # turn all stats to strings
    overall_stats = {k: str(v) for k, v in overall_stats.items()}

    current_prompt = current_prompt.replace("{GAME_NAME_HERE}", game_name)
    current_prompt = current_prompt.replace("{GAME_AVERAGE_HERE}", game_mean)
    current_prompt = current_prompt.replace("{TWO_UNDER}", overall_stats["two_under"])
    current_prompt = current_prompt.replace("{ONE_UNDER}", overall_stats["one_under"])
    current_prompt = current_prompt.replace("{ONE_OVER}", overall_stats["one_over"])
    current_prompt = current_prompt.replace("{HALF_OVER}", overall_stats["half_over"])
    current_prompt = current_prompt.replace(
        "{OVERALL_MEAN}", overall_stats["overall_mean"]
    )
    return current_prompt


def get_single_game_entries(
    df: pd.DataFrame, game_id: str, sample_pct: float = 0.1
) -> Tuple[pd.DataFrame, str, str]:

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

    print(f"Total quality reviews: {len(df)}")

    sample_size = sample_size if sample_size >= 250 else len(df)

    if sample_size == len(df):
        print("Using all quality reviews")
    elif len(df) < sample_size:
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

    avg_rating = str(round(df["AvgRating"].iloc[0], 1))
    df = df[["BGGId", "Description", "combined_review"]]

    return df, game_name, avg_rating
