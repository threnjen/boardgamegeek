import os
import time

from dagster import ConfigurableResource, asset, get_dagster_logger, op

logger = get_dagster_logger()

ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
WORKING_ENV_DIR = "data/prod/" if ENVIRONMENT == "prod" else "data/test/"


@asset
def bgg_games_csv(
    s3_resource: ConfigurableResource,
    lambda_resource: ConfigurableResource,
    config_resource: ConfigurableResource,
) -> bool:
    """
    Triggers the lambda to get the games file from the BoardGameGeek website
    """

    logger.info("Getting the games csv file from BoardGameGeek")

    configs = config_resource.get_config_file()

    s3_scraper_bucket = configs["s3_scraper_bucket"]

    original_timestamps = {
        f'{WORKING_ENV_DIR}{configs["boardgamegeek_csv_filename"]}': s3_resource.get_last_modified(
            bucket=s3_scraper_bucket,
            key=f'{WORKING_ENV_DIR}{configs["boardgamegeek_csv_filename"]}',
        )
    }

    logger.info("Invoking lambda to refresh file...")

    lambda_resource.invoke_lambda(function=configs["file_retrieval_lambda"])

    logger.info("Lambda invoked. Beginning timestamp checks...")

    return compare_timestamps_for_refresh(
        original_timestamps=original_timestamps,
        file_list_to_check=[
            f'{WORKING_ENV_DIR}{configs["boardgamegeek_csv_filename"]}'
        ],
        location_bucket=s3_scraper_bucket,
        sleep_timer=15,
        s3_resource=s3_resource,
    )


@asset(deps=["bgg_games_csv"])
def game_scraper_urls(
    lambda_resource: ConfigurableResource,
    s3_resource: ConfigurableResource,
    config_resource: ConfigurableResource,
) -> bool:
    """
    Generates the game scraper keys that should exist.
    Gets the last modified timestamp of each keys from s3.
    Runs the lambda function to generate the urls.
    Waits for the urls to be generated.
    Polls S3 for the last modified timestamp of the keys.
    If the last modified timestamp of the keys is greater than the last modified timestamp of the keys in s3.
    Then the keys have been updated and the asset is materialized.
    Every time a timestamp is found to be greater than the last modified timestamp in s3, remove that key from the check dictionary so it is not checked again.
    Update the last modified timestamp of the keys in s3.
    """

    logger.info("Generating game scraper urls")

    configs = config_resource.get_config_file()

    s3_scraper_bucket = configs["s3_scraper_bucket"]
    raw_urls_directory = configs["game"]["raw_urls_directory"]
    output_urls_json_suffix = configs["game"]["output_urls_json_suffix"]

    game_scraper_url_filenames = (
        [
            f"{raw_urls_directory}/group{i}{output_urls_json_suffix}"
            for i in range(1, 31)
        ]
        if ENVIRONMENT == "prod"
        else [f"{raw_urls_directory}/group1{output_urls_json_suffix}"]
    )

    create_new_urls(
        lambda_resource,
        s3_resource,
        s3_scraper_bucket,
        game_scraper_url_filenames,
        lambda_function_name="bgg_generate_game_urls",
    )

    return True


@asset(deps=["game_scraper_urls"])
def scraped_game_xmls(
    ecs_resource: ConfigurableResource,
    s3_resource: ConfigurableResource,
    config_resource: ConfigurableResource,
) -> bool:
    """
    Scrapes the BGG website for game data, using the URLs generated in the previous step
    """

    configs = config_resource.get_config_file()

    scrape_data(ecs_resource, s3_resource, configs, scraper_type="game")

    return True


@asset(deps=["scraped_game_xmls"])
def game_dfs_clean(
    s3_resource: ConfigurableResource,
    ecs_resource: ConfigurableResource,
    config_resource: ConfigurableResource,
) -> bool:
    """
    Creates dirty dataframes for the game data from the scraped XML
    """

    configs = config_resource.get_config_file()

    bucket = configs["s3_scraper_bucket"]
    key = f'{WORKING_ENV_DIR}{configs["game"]["output_xml_directory"]}'
    data_sets = configs["game"]["data_sets"]

    raw_game_files = s3_resource.list_file_keys(bucket=bucket, key=key)

    assert len(raw_game_files) == 30 if ENVIRONMENT == "prod" else 1

    task_definition = (
        "bgg_game_data_cleaner"
        if ENVIRONMENT == "prod"
        else "dev_bgg_game_data_cleaner"
    )

    ecs_resource.launch_ecs_task(task_definition=task_definition)

    logger.info(data_sets)

    data_set_file_names = [
        f"{WORKING_ENV_DIR}{configs['game']['clean_dfs_directory']}/{x}_clean.pkl"
        for x in data_sets
    ]
    logger.info(data_set_file_names)

    original_timestamps = {
        key: s3_resource.get_last_modified(
            bucket=bucket,
            key=key,
        )
        for key in data_set_file_names
    }

    compare_timestamps_for_refresh(
        original_timestamps=original_timestamps,
        file_list_to_check=data_set_file_names,
        location_bucket=bucket,
        sleep_timer=300,
        s3_resource=s3_resource,
    )

    return True


@asset(deps=["game_dfs_clean"])
def user_scraper_urls(
    lambda_resource: ConfigurableResource,
    s3_resource: ConfigurableResource,
    config_resource: ConfigurableResource,
) -> bool:
    """
    Generates the user scraper keys that should exist.
    Gets the last modified timestamp of each keys from s3.
    Runs the lambda function to generate the urls.
    Waits for the urls to be generated.
    Polls S3 for the last modified timestamp of the keys.
    If the last modified timestamp of the keys is greater than the last modified timestamp of the keys in s3.
    Then the keys have been updated and the asset is materialized.
    Every time a timestamp is found to be greater than the last modified timestamp in s3, remove that key from the check dictionary so it is not checked again.
    Update the last modified timestamp of the keys in s3.
    """

    configs = config_resource.get_config_file()

    s3_scraper_bucket = configs["s3_scraper_bucket"]
    raw_urls_directory = configs["user"]["raw_urls_directory"]
    output_urls_json_suffix = configs["user"]["output_urls_json_suffix"]

    user_scraper_url_filenames = (
        [
            f"{raw_urls_directory}/group{i}{output_urls_json_suffix}"
            for i in range(1, 31)
        ]
        if ENVIRONMENT == "prod"
        else [f"{raw_urls_directory}/group1{output_urls_json_suffix}"]
    )

    create_new_urls(
        lambda_resource,
        s3_resource,
        s3_scraper_bucket,
        user_scraper_url_filenames,
        lambda_function_name="bgg_generate_user_urls",
    )

    return True


@asset(deps=["user_scraper_urls"])
def scraped_user_xmls(
    ecs_resource: ConfigurableResource,
    s3_resource: ConfigurableResource,
    config_resource: ConfigurableResource,
) -> bool:
    """
    Scrapes the BGG website for user data, using the URLs generated in the previous step
    """

    configs = config_resource.get_config_file()

    scrape_data(ecs_resource, s3_resource, configs, scraper_type="user")

    return True


@op
def compare_timestamps_for_refresh(
    original_timestamps: dict,
    file_list_to_check: list[str],
    location_bucket: str,
    sleep_timer: int,
    s3_resource: ConfigurableResource,
) -> bool:
    new_timestamp_tracker = {}

    logger.info("Checking timestamps...")

    while len(file_list_to_check):

        time.sleep(sleep_timer)

        logger.info(f"Files to check: {file_list_to_check}")
        for key in file_list_to_check:
            logger.info(f"Checking key: {key}")
            new_timestamp_tracker[key] = s3_resource.get_last_modified(
                bucket=location_bucket,
                key=key,
            )

        for key in original_timestamps:
            new_date = new_timestamp_tracker[key]
            old_date = original_timestamps[key]
            if new_date > old_date:
                logger.info(
                    f"new timestamp {new_date} is greater than old timestamp {old_date}"
                )
                if key in file_list_to_check:
                    file_list_to_check.remove(key)

    return True


@op
def create_new_urls(
    lambda_resource: ConfigurableResource,
    s3_resource: ConfigurableResource,
    s3_scraper_bucket: str,
    scraper_url_filenames: list[str],
    lambda_function_name: str,
) -> bool:

    scraper_url_filenames = [f"{WORKING_ENV_DIR}{x}" for x in scraper_url_filenames]
    logger.info(f"Created location urls for {scraper_url_filenames}")

    original_timestamps = {
        key: s3_resource.get_last_modified(
            bucket=s3_scraper_bucket,
            key=key,
        )
        for key in scraper_url_filenames
    }
    logger.info(f"Original timestamps: {original_timestamps}")

    lambda_function_name = (
        lambda_function_name if ENVIRONMENT == "prod" else f"dev_{lambda_function_name}"
    )

    lambda_resource.invoke_lambda(function=lambda_function_name)

    compare_timestamps_for_refresh(
        original_timestamps=original_timestamps,
        file_list_to_check=scraper_url_filenames,
        location_bucket=s3_scraper_bucket,
        sleep_timer=15,
        s3_resource=s3_resource,
    )

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

    input_urls_key = f"{WORKING_ENV_DIR}{input_urls_key}"

    scraper_raw_data_filenames = (
        [
            f"{WORKING_ENV_DIR}{output_key_directory}/{output_key_suffix.format(f'group{i}')}"
            for i in range(1, 31)
        ]
        if ENVIRONMENT == "prod"
        else [
            f"{WORKING_ENV_DIR}{output_key_directory}/{output_key_suffix.format('group1')}"
        ]
    )

    original_timestamps = {
        key: s3_resource.get_last_modified(
            bucket=bucket,
            key=key,
        )
        for key in scraper_raw_data_filenames
    }

    logger.info(f"Original timestamps: {original_timestamps}")

    game_scraper_url_filenames = s3_resource.list_file_keys(
        bucket=bucket, key=input_urls_key
    )

    task_definition = configs["scraper_task_definition"]
    task_definition = (
        task_definition if ENVIRONMENT == "prod" else f"dev_{task_definition}"
    )
    logger.info(task_definition)

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
        logger.info(f"Launched ECS for filename: {filename}")

    compare_timestamps_for_refresh(
        original_timestamps=original_timestamps,
        file_list_to_check=scraper_raw_data_filenames,
        location_bucket=bucket,
        sleep_timer=300,
        s3_resource=s3_resource,
    )

    return True


# @multi_asset(specs=[AssetSpec("asset1"), AssetSpec("asset2")])
# def materialize_1_and_2():
#     materialize_asset_1()
#     yield MaterializeResult("asset1")
#     materialize_asset_2_expensively() # could take hours
#     yield MaterializeResult("asset2")
