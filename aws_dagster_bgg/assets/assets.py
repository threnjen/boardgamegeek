from dagster import asset, ConfigurableResource, op
import time


@asset
def bgg_games_csv(
    s3_resource: ConfigurableResource,
    lambda_resource: ConfigurableResource,
    config_resource: ConfigurableResource,
) -> bool:
    f"""Triggers the lambda to get the games file from the BoardGameGeek website"""

    configs = config_resource.get_config_file()

    s3_scraper_bucket = configs["s3_scraper_bucket"]

    modification_timestamp = s3_resource.get_last_modified(
        bucket=s3_scraper_bucket,
        key=configs["boardgamegeek_csv_filename"],
    )

    lambda_resource.invoke_lambda(function=configs["file_retrieval_lambda"])

    time.sleep(15)

    while True:
        new_modification_timestamp = s3_resource.get_last_modified(
            bucket=s3_scraper_bucket,
            key=configs["boardgamegeek_csv_filename"],
        )

        if new_modification_timestamp > modification_timestamp:
            break

        time.sleep(15)

    return True


@asset(deps=["bgg_games_csv"])
def game_scraper_urls(
    # dynamodb_resource: ConfigurableResource,
    lambda_resource: ConfigurableResource,
    s3_resource: ConfigurableResource,
    config_resource: ConfigurableResource,
) -> bool:
    """
    Generates the game scraper keys that should exist
    Gets the last modified timestamp of each keys from dynamodb
    Runs the lambda function to generate the urls
    Waits for the urls to be generated
    Polls S3 for the last modified timestamp of the keys
    If the last modified timestamp of the keys is greater than the last modified timestamp of the keys in dynamodb
    Then the keys have been updated and the asset is materialized
    Every time a timestamp is found to be greater than the last modified timestamp in dynamodb, remove that key from the check dictionary so it is not checked again
    Update the last modified timestamp of the keys in dynamodb
    """

    configs = config_resource.get_config_file()

    s3_scraper_bucket = configs["s3_scraper_bucket"]
    raw_urls_directory = configs["game"]["raw_urls_directory"]
    output_urls_json_suffix = configs["game"]["output_urls_json_suffix"]

    game_scraper_url_filenames = [
        f"{raw_urls_directory}/group{i}{output_urls_json_suffix}" for i in range(1, 31)
    ]

    timestamp_tracker = {
        key: s3_resource.get_last_modified(
            bucket=s3_scraper_bucket,
            key=key,
        )
        for key in game_scraper_url_filenames
    }
    lambda_resource.invoke_lambda(function="bgg_generate_game_urls")

    time.sleep(15)

    new_timestamp_tracker = {}

    while len(game_scraper_url_filenames):
        for key in game_scraper_url_filenames:
            new_timestamp_tracker[key] = s3_resource.get_last_modified(
                bucket=s3_scraper_bucket,
                key=key,
            )

        for key in timestamp_tracker:
            new_date = new_timestamp_tracker[key]
            old_date = timestamp_tracker[key]
            if new_date > old_date:
                print(
                    f"new timestamp {new_date} is greater than old timestamp {old_date}"
                )
                if key in game_scraper_url_filenames:
                    game_scraper_url_filenames.remove(key)

        time.sleep(15)

    return True


@asset(deps=["game_scraper_urls"])
def scrape_game_data(
    ecs_resource: ConfigurableResource,
    s3_resource: ConfigurableResource,
    config_resource: ConfigurableResource,
) -> bool:

    configs = config_resource.get_config_file()

    scrape_data(ecs_resource, s3_resource, configs, scraper_type="game")

    return True


@op
def scrape_data(
    ecs_resource: ConfigurableResource,
    s3_resource: ConfigurableResource,
    configs: dict,
    scraper_type: str,
) -> bool:

    bucket = configs["s3_scraper_bucket"]
    input_urls_key = configs[scraper_type]["raw_urls_directory"]
    output_key_directory = configs[scraper_type]["output_xml_directory"]
    output_key_suffix = configs[scraper_type]["output_raw_xml_suffix"]

    scraper_raw_data_filenames = [
        f"{output_key_directory}/{output_key_suffix.format(i)}" for i in range(1, 31)
    ]

    timestamp_tracker = {
        key: s3_resource.get_last_modified(
            bucket=bucket,
            key=key,
        )
        for key in scraper_raw_data_filenames
    }

    game_scraper_url_filenames = s3_resource.list_file_keys(
        bucket=bucket, key=input_urls_key
    )

    task_definition = configs["scraper_task_definition"]

    for key in game_scraper_url_filenames:
        filename = key.split("/")[-1].split(".")[0]

        overrides = {
            "containerOverrides": [
                {
                    "name": task_definition,
                    "environment": [
                        {"name": "FILENAME", "value": filename},
                        {"name": "SCRAPER_TYPE", "value": scraper_type},
                    ],
                }
            ]
        }
        ecs_resource.launch_ecs_task(task_definition, overrides)

    time.sleep(60 * 30)

    new_timestamp_tracker = {}

    while len(scraper_raw_data_filenames):

        for key in scraper_raw_data_filenames:
            new_timestamp_tracker[key] = s3_resource.get_last_modified(
                bucket=bucket,
                key=key,
            )

        for key in timestamp_tracker:
            new_date = new_timestamp_tracker[key]
            old_date = timestamp_tracker[key]
            if new_date > old_date:
                print(
                    f"new timestamp {new_date} is greater than old timestamp {old_date}"
                )
                if key in scraper_raw_data_filenames:
                    scraper_raw_data_filenames.remove(key)

        time.sleep(60 * 5)

    return True


@asset
def game_dfs_dirty(
    s3_resource: ConfigurableResource,
    ecs_resource: ConfigurableResource,
    config_resource: ConfigurableResource,
) -> bool:
    """
    Creates dirty dataframes for the game data
    """

    configs = config_resource.get_config_file()

    bucket = configs["s3_scraper_bucket"]
    key = configs["game"]["output_xml_directory"]

    raw_game_files = s3_resource.list_file_keys(bucket=bucket, key=key)

    assert len(raw_game_files) == 30

    ecs_resource.launch_ecs_task("boardgamegeek_cleaner", {})


# @multi_asset(specs=[AssetSpec("asset1"), AssetSpec("asset2")])
# def materialize_1_and_2():
#     materialize_asset_1()
#     yield MaterializeResult("asset1")
#     materialize_asset_2_expensively() # could take hours
#     yield MaterializeResult("asset2")
