import os
import sys

import boto3

from config import CONFIGS

ENV = os.environ.get("ENV", "dev")
S3_SCRAPER_BUCKET = CONFIGS["s3_scraper_bucket"]
SCRAPER_TASK_DEFINITION = CONFIGS["scraper_task_definition"]


def get_filenames(scraper_type):
    """Get the filenames of the files to be processed by the scraper"""

    if ENV == "dev":
        raw_files = os.listdir(
            f"local_data/{CONFIGS[scraper_type]['raw_urls_directory']}"
        )
        file_prefixes = [x for x in raw_files if x.endswith(".json")]
    else:
        s3_client = boto3.client("s3")
        raw_files = s3_client.list_objects_v2(
            Bucket=S3_SCRAPER_BUCKET, Prefix=CONFIGS[scraper_type]["raw_urls_directory"]
        )["Contents"]
        file_prefixes = [x["Key"] for x in raw_files]

    return file_prefixes


def lambda_handler(event, context):
    """Trigger the Fargate task to process the files in the S3 bucket"""

    scraper_type = event.get("scraper_type")

    print(f"Running scraper for {scraper_type}")

    # TO DO LATER: HAVE THIS TRIGGER OFF OF EACH FILE LANDING AND SPAWN TASKS IN PARALLEL INSTEAD OF READING THE DIRECTORY

    file_prefixes = get_filenames(scraper_type)
    print(file_prefixes)

    task_definition = (
        f"{SCRAPER_TASK_DEFINITION}-dev" if ENV != "prod" else SCRAPER_TASK_DEFINITION
    )
    print(task_definition)

    ecs_client = boto3.client("ecs", region_name="us-west-2")

    latest_version = (
        ecs_client.describe_task_definition(taskDefinition=task_definition)
        .get("taskDefinition")
        .get("revision")
    )

    for file in file_prefixes:
        filename = file.split("/")[-1].split(".")[0]
        print(filename)

        response = ecs_client.run_task(
            taskDefinition=f"{task_definition}:{latest_version}",
            cluster="boardgamegeek",
            launchType="FARGATE",
            count=1,
            platformVersion="LATEST",
            enableECSManagedTags=False,
            networkConfiguration={
                "awsvpcConfiguration": {
                    "subnets": ["subnet-024f9d00c25a8f8b9", "subnet-0f1216cb6edc82e8f"],
                    "securityGroups": [
                        "sg-0c40df16e4dcae91b",
                    ],
                    "assignPublicIp": "ENABLED",
                },
            },
            overrides={
                "containerOverrides": [
                    {
                        "name": task_definition,
                        "environment": [
                            {"name": "FILENAME", "value": filename},
                            {"name": "SCRAPER_TYPE", "value": scraper_type},
                        ],
                    }
                ]
            },
        )


if __name__ == "__main__":
    scraper_type = sys.argv[1]

    event = {"scraper_type": scraper_type}

    lambda_handler(event, None)
