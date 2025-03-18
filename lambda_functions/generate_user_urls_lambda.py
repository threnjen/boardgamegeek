import os
from datetime import datetime

from config import CONFIGS
from utils.processing_functions import (load_file_local_first,
                                        save_file_local_first)

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
S3_SCRAPER_BUCKET = CONFIGS["s3_scraper_bucket"]
USER_CONFIGS = CONFIGS["users"]
url_block_size = 20
number_url_files = 29
NUMBER_PROCESSES = 29


def generate_user_urls(user_ids):
    """Generate the raw urls for the scraper"""

    urls_list = []

    for user_id in user_ids:
        path = f"https://boardgamegeek.com/xmlapi2/collection?username={user_id}&rated=1&stats=1"
        urls_list.append(path)

    return urls_list


def lambda_handler(event, context):
    """Generate the raw URLs for the ratings scraper
    This function will read the game ids from the local csv file or S3
    and generate the raw URLs for the ratings scraper. The URLs
    will be split into blocks and saved to S3 for the scraper
    to pick up."""

    timestamp = datetime.now().strftime("%Y%m%d") = datetime.now().strftime("%Y%m%d")
    users = load_file_local_first(
        path=f"ratings",
        file_name=f"unique_ids_{timestamp}.json",
    )

    user_ids = list(users.values())[0]
    print(type(user_ids))
    print(f"\nNumber of user ids: {len(user_ids)}\n")

    total_url_files = 29
    total_users = len(user_ids)
    urls_per_file = total_users // total_url_files

    print(f"urls per file {urls_per_file}")

    # generate blocks of urls
    url_blocks = {}

    total_users_processed = 0
    block = 0

    for i in range(0, total_url_files):
        group_num = i + 1
        url_blocks[group_num] = user_ids[block : block + urls_per_file]

        print(f"{len(url_blocks[group_num])} users in group{group_num}")
        group_urls = generate_user_urls(url_blocks[group_num])

        if ENVIRONMENT != "prod":
            group_urls = group_urls[:20]

        save_file_local_first(
            path=USER_CONFIGS["raw_urls_directory"],
            file_name=f"group{group_num}{USER_CONFIGS['output_urls_json_suffix']}",
            data=group_urls,
        )

        total_users_processed += len(url_blocks[group_num])

        block += urls_per_file

        if ENVIRONMENT != "prod":
            break

    print(f"\nTotal users processed: {total_users_processed}")


if __name__ == "__main__":
    lambda_handler(None, None)
