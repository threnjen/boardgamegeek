import os
import time

from dagster import ConfigurableResource, asset, get_dagster_logger, op

logger = get_dagster_logger()

ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
WORKING_ENV_DIR = "data/prod/" if ENVIRONMENT == "prod" else "data/test/"
S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")
REFRESH = 300 if ENVIRONMENT == "prod" else 30


@asset
def boardgame_ranks_csv(
    s3_resource: ConfigurableResource,
    lambda_resource: ConfigurableResource,
    config_resource: ConfigurableResource,
) -> bool:
    """
    Triggers the lambda to get the games file from the BoardGameGeek website
    """

    logger.info("Getting the games csv file from BoardGameGeek")

    configs = config_resource.get_config_file()

    s3_scraper_bucket = S3_SCRAPER_BUCKET

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


@asset(deps=["boardgame_ranks_csv"])
def games_scraper_urls_raw(
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

    games_configs = config_resource.get_config_file()["games"]

    s3_scraper_bucket = S3_SCRAPER_BUCKET
    raw_urls_directory = games_configs["raw_urls_directory"]
    output_urls_json_suffix = games_configs["output_urls_json_suffix"]

    game_scraper_url_filenames = (
        [
            f"{raw_urls_directory}/group{i}{output_urls_json_suffix}"
            for i in range(1, 30)
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


@asset(deps=["games_scraper_urls_raw"])
def games_scraped_xml_raw(
    ecs_resource: ConfigurableResource,
    s3_resource: ConfigurableResource,
    config_resource: ConfigurableResource,
) -> bool:
    """
    Scrapes the BGG website for game data, using the URLs generated in the previous step
    """

    configs = config_resource.get_config_file()

    scrape_data(ecs_resource, s3_resource, configs, scraper_type="games")

    return True


@asset(deps=["games_scraped_xml_raw"])
def games_combined_xml(
    ecs_resource: ConfigurableResource,
    s3_resource: ConfigurableResource,
    config_resource: ConfigurableResource,
) -> bool:
    """Combines the smaller xml files into large xml files"""

    games_configs = config_resource.get_config_file()["games"]

    s3_scraper_bucket = S3_SCRAPER_BUCKET

    task_definition = (
        "bgg_xml_cleanup" if ENVIRONMENT == "prod" else "dev_bgg_xml_cleanup"
    )

    overrides = {
        "containerOverrides": [
            {
                "name": task_definition,
                "environment": [
                    {"name": "SCRAPER_TYPE", "value": "games"},
                ],
            }
        ]
    }

    ecs_resource.launch_ecs_task(task_definition=task_definition, overrides=overrides)

    data_set_file_names = (
        [
            f"{WORKING_ENV_DIR}{games_configs['output_xml_directory']}/{games_configs['output_raw_xml_suffix'].replace("{}", f'group{x}')}"
            for x in range(30)
        ]
        if ENVIRONMENT == "prod"
        else [
            f"{WORKING_ENV_DIR}{games_configs['output_xml_directory']}/{games_configs['output_raw_xml_suffix'].replace('{}', 'group1')}"
        ]
    )

    logger.info(data_set_file_names)

    original_timestamps = {
        key: s3_resource.get_last_modified(
            bucket=s3_scraper_bucket,
            key=key,
        )
        for key in data_set_file_names
    }

    compare_timestamps_for_refresh(
        original_timestamps=original_timestamps,
        file_list_to_check=data_set_file_names,
        location_bucket=s3_scraper_bucket,
        sleep_timer=REFRESH,
        s3_resource=s3_resource,
    )

    return True


@asset(deps=["games_combined_xml"])
def game_dfs_clean(
    s3_resource: ConfigurableResource,
    ecs_resource: ConfigurableResource,
    config_resource: ConfigurableResource,
) -> bool:
    """
    Creates dirty dataframes for the game data from the scraped XML
    """

    games_configs = config_resource.get_config_file()["games"]

    s3_scraper_bucket = S3_SCRAPER_BUCKET

    data_sets = games_configs["data_sets"]

    task_definition = (
        "bgg_data_cleaner_game"
        if ENVIRONMENT == "prod"
        else "dev_bgg_data_cleaner_game"
    )

    ecs_resource.launch_ecs_task(task_definition=task_definition)

    logger.info(data_sets)

    data_set_file_names = [
        f"{WORKING_ENV_DIR}{games_configs['clean_dfs_directory']}/{x}_clean.pkl"
        for x in data_sets
    ]
    logger.info(data_set_file_names)

    original_timestamps = {
        key: s3_resource.get_last_modified(
            bucket=s3_scraper_bucket,
            key=key,
        )
        for key in data_set_file_names
    }

    compare_timestamps_for_refresh(
        original_timestamps=original_timestamps,
        file_list_to_check=data_set_file_names,
        location_bucket=s3_scraper_bucket,
        sleep_timer=REFRESH,
        s3_resource=s3_resource,
    )

    return True


@asset(deps=["game_dfs_clean"])
def ratings_scraper_urls_raw(
    lambda_resource: ConfigurableResource,
    s3_resource: ConfigurableResource,
    config_resource: ConfigurableResource,
) -> bool:
    """
    Generates the ratings scraper keys that should exist.
    Gets the last modified timestamp of each keys from s3.
    Runs the lambda function to generate the urls.
    Waits for the urls to be generated.
    Polls S3 for the last modified timestamp of the keys.
    If the last modified timestamp of the keys is greater than the last modified timestamp of the keys in s3.
    Then the keys have been updated and the asset is materialized.
    Every time a timestamp is found to be greater than the last modified timestamp in s3, remove that key from the check dictionary so it is not checked again.
    Update the last modified timestamp of the keys in s3.
    """

    rating_configs = config_resource.get_config_file()["ratings"]

    s3_scraper_bucket = S3_SCRAPER_BUCKET
    raw_urls_directory = rating_configs["raw_urls_directory"]
    output_urls_json_suffix = rating_configs["output_urls_json_suffix"]

    ratings_scraper_url_filenames = (
        [
            f"{raw_urls_directory}/group{i}{output_urls_json_suffix}"
            for i in range(1, 30)
        ]
        if ENVIRONMENT == "prod"
        else [f"{raw_urls_directory}/group1{output_urls_json_suffix}"]
    )

    create_new_urls(
        lambda_resource,
        s3_resource,
        s3_scraper_bucket,
        ratings_scraper_url_filenames,
        lambda_function_name="bgg_generate_ratings_urls",
    )

    return True


@asset(deps=["ratings_scraper_urls_raw"])
def ratings_scraped_xml_raw(
    ecs_resource: ConfigurableResource,
    s3_resource: ConfigurableResource,
    config_resource: ConfigurableResource,
) -> bool:
    """
    Scrapes the BGG website for ratings data, using the URLs generated in the previous step
    """

    configs = config_resource.get_config_file()

    scrape_data(ecs_resource, s3_resource, configs, scraper_type="ratings")

    return True


@asset(deps=["ratings_scraped_xml_raw"])
def ratings_combined_xml(
    ecs_resource: ConfigurableResource,
    s3_resource: ConfigurableResource,
    config_resource: ConfigurableResource,
) -> bool:
    """Combines the smaller xml files into large xml files"""

    rating_configs = config_resource.get_config_file()["ratings"]

    s3_scraper_bucket = S3_SCRAPER_BUCKET

    task_definition = (
        "bgg_xml_cleanup" if ENVIRONMENT == "prod" else "dev_bgg_xml_cleanup"
    )

    overrides = {
        "containerOverrides": [
            {
                "name": task_definition,
                "environment": [
                    {"name": "SCRAPER_TYPE", "value": "ratings"},
                ],
            }
        ]
    }

    ecs_resource.launch_ecs_task(task_definition=task_definition, overrides=overrides)

    data_set_file_names = (
        [
            f"{WORKING_ENV_DIR}{rating_configs['output_xml_directory']}/{rating_configs['output_raw_xml_suffix'].replace("{}", f'group{x}')}"
            for x in range(30)
        ]
        if ENVIRONMENT == "prod"
        else [
            f"{WORKING_ENV_DIR}{rating_configs['output_xml_directory']}/{rating_configs['output_raw_xml_suffix'].replace('{}', 'group1')}"
        ]
    )

    logger.info(data_set_file_names)

    original_timestamps = {
        key: s3_resource.get_last_modified(
            bucket=s3_scraper_bucket,
            key=key,
        )
        for key in data_set_file_names
    }

    compare_timestamps_for_refresh(
        original_timestamps=original_timestamps,
        file_list_to_check=data_set_file_names,
        location_bucket=s3_scraper_bucket,
        sleep_timer=REFRESH,
        s3_resource=s3_resource,
    )

    return True


@asset(deps=["ratings_combined_xml"])
def ratings_dfs_dirty(
    s3_resource: ConfigurableResource,
    ecs_resource: ConfigurableResource,
    config_resource: ConfigurableResource,
) -> bool:
    """
    Creates a clean dataframe for the ratings data from the scraped ratings XML files
    """

    rating_configs = config_resource.get_config_file()["ratings"]

    s3_scraper_bucket = S3_SCRAPER_BUCKET
    key = f'{WORKING_ENV_DIR}{rating_configs["output_xml_directory"]}'

    raw_ratings_files = s3_resource.list_file_keys(bucket=s3_scraper_bucket, key=key)

    assert len(raw_ratings_files) == 29 if ENVIRONMENT == "prod" else 1

    task_definition = (
        "bgg_data_cleaner_ratings"
        if ENVIRONMENT == "prod"
        else "dev_bgg_data_cleaner_ratings"
    )

    ecs_resource.launch_ecs_task(task_definition=task_definition)

    check_filenames = [
        f"{WORKING_ENV_DIR}{rating_configs['dirty_dfs_directory']}/{rating_configs['ratings_save_file']}"
    ]
    logger.info(check_filenames)

    original_timestamps = {
        key: s3_resource.get_last_modified(
            bucket=s3_scraper_bucket,
            key=key,
        )
        for key in check_filenames
    }

    compare_timestamps_for_refresh(
        original_timestamps=original_timestamps,
        file_list_to_check=check_filenames,
        location_bucket=s3_scraper_bucket,
        sleep_timer=REFRESH,
        s3_resource=s3_resource,
    )

    return True


@asset(deps=["ratings_dfs_dirty"])
def dynamodb_store(
    ecs_resource: ConfigurableResource,
    # config_resource: ConfigurableResource,
) -> bool:

    task_definition = (
        "bgg_dynamodb_data_store"
        if ENVIRONMENT == "prod"
        else "dev_bgg_dynamodb_data_store"
    )

    ecs_resource.launch_ecs_task(task_definition=task_definition)
    return True


@asset
def users_scraper_urls_raw(
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

    logger.info("Generating user scraper urls")

    configs = config_resource.get_config_file()

    s3_scraper_bucket = S3_SCRAPER_BUCKET
    raw_urls_directory = configs["users"]["raw_urls_directory"]
    output_urls_json_suffix = configs["users"]["output_urls_json_suffix"]

    game_scraper_url_filenames = (
        [
            f"{raw_urls_directory}/group{i}{output_urls_json_suffix}"
            for i in range(1, 30)
        ]
        if ENVIRONMENT == "prod"
        else [f"{raw_urls_directory}/group1{output_urls_json_suffix}"]
    )

    create_new_urls(
        lambda_resource,
        s3_resource,
        s3_scraper_bucket,
        game_scraper_url_filenames,
        lambda_function_name="bgg_generate_user_urls",
    )

    return True


@asset(deps=["users_scraper_urls_raw"])
def users_scraped_xml_raw(
    ecs_resource: ConfigurableResource,
    s3_resource: ConfigurableResource,
    config_resource: ConfigurableResource,
) -> bool:
    """
    Scrapes the BGG website for users data, using the URLs generated in the previous step
    """

    configs = config_resource.get_config_file()

    scrape_data(ecs_resource, s3_resource, configs, scraper_type="users")

    return True


@asset(deps=["users_scraped_xml_raw"])
def user_dfs_dirty(
    s3_resource: ConfigurableResource,
    ecs_resource: ConfigurableResource,
    config_resource: ConfigurableResource,
) -> bool:
    """
    Creates a clean dataframe for the ratings data from the scraped ratings XML files
    """

    configs = config_resource.get_config_file()

    s3_scraper_bucket = S3_SCRAPER_BUCKET

    task_definition = (
        "bgg_data_cleaner_users"
        if ENVIRONMENT == "prod"
        else "dev_bgg_data_cleaner_users"
    )

    ecs_resource.launch_ecs_task(task_definition=task_definition)

    check_filenames = [
        f"{WORKING_ENV_DIR}{configs['users']['clean_dfs_directory']}/complete_user_ratings.pkl"
    ]
    logger.info(check_filenames)

    original_timestamps = {
        key: s3_resource.get_last_modified(
            bucket=s3_scraper_bucket,
            key=key,
        )
        for key in check_filenames
    }

    compare_timestamps_for_refresh(
        original_timestamps=original_timestamps,
        file_list_to_check=check_filenames,
        location_bucket=s3_scraper_bucket,
        sleep_timer=REFRESH,
        s3_resource=s3_resource,
    )

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

        logger.info(f"Files to check: {file_list_to_check}")

        time.sleep(sleep_timer)

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

    s3_scraper_bucket = S3_SCRAPER_BUCKET
    input_urls_key = configs[scraper_type]["raw_urls_directory"]

    input_urls_key = f"{WORKING_ENV_DIR}{input_urls_key}"

    game_scraper_url_filenames = s3_resource.list_file_keys(
        bucket=s3_scraper_bucket, key=input_urls_key
    )

    task_definition = configs["scraper_task_definition"]
    task_definition = (
        task_definition if ENVIRONMENT == "prod" else f"dev_{task_definition}"
    )
    logger.info(task_definition)
    logger.info(len(game_scraper_url_filenames))
    logger.info(game_scraper_url_filenames)

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
        time.sleep(10)
        logger.info(f"Launched ECS for filename: {filename}")

    time.sleep(30)

    def get_total_tasks():
        count_running_tasks = ecs_resource.count_running_tasks(status="RUNNING")
        count_pending_tasks = ecs_resource.count_running_tasks(status="PENDING")
        return count_running_tasks + count_pending_tasks

    allowed_tasks = 2 if os.environ.get("IS_LOCAL", "true").lower() == "false" else 1

    while get_total_tasks() >= allowed_tasks:
        logger.info(f"Waiting for tasks to finish. {get_total_tasks()} running")
        time.sleep(REFRESH)

    return True


# @multi_asset(specs=[AssetSpec("asset1"), AssetSpec("asset2")])
# def materialize_1_and_2():
#     materialize_asset_1()
#     yield MaterializeResult("asset1")
#     materialize_asset_2_expensively() # could take hours
#     yield MaterializeResult("asset2")
