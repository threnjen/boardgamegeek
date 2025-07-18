import os
import sys

import boto3

from config import CONFIGS
from utils.processing_functions import get_s3_keys_based_on_env
from utils.s3_file_handler import S3FileHandler

ENVIRONMENT = os.environ.get("TF_VAR_RESOURCE_ENV" "dev")
S3_SCRAPER_BUCKET = CONFIGS["s3_scraper_bucket"]
TERRAFORM_STATE_BUCKET = CONFIGS["terraform_state_bucket"]
WORKING_DIR = f"data/{ENVIRONMENT}/"


def lambda_handler(event, context):
    """Trigger the Fargate task to process the files in the S3 bucket"""

    data_type = event.get("data_type")

    print(f"Running scraper for {data_type}")

    terraform_state_file = S3FileHandler().load_tfstate(
        file_path=CONFIGS["terraform_state_file"]
    )

    print(terraform_state_file["outputs"])

    if not event.get("file_name"):
        file_prefixes = get_s3_keys_based_on_env(
            directory=f'{CONFIGS[data_type]["raw_urls_directory"]}'
        )

    else:
        file_name = event.get("file_name")
        file_prefixes = [
            f"{WORKING_DIR}{CONFIGS[data_type]['raw_urls_directory']}/{file_name}"
        ]

    task_definition = f'{CONFIGS["scraper_task_definition"]}_{ENVIRONMENT}'

    print(task_definition)

    ecs_client = boto3.client("ecs")

    latest_version = (
        ecs_client.describe_task_definition(taskDefinition=task_definition)
        .get("taskDefinition")
        .get("revision")
    )

    if ENVIRONMENT != "prod":
        file_prefixes = file_prefixes[:1]

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
                    "subnets": terraform_state_file["outputs"]["public_subnets"][
                        "value"
                    ],
                    "securityGroups": [
                        terraform_state_file["outputs"]["sg_ec2_ssh_access"]["value"]
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
                            {"name": "DATA_TYPE", "value": data_type},
                        ],
                    }
                ]
            },
        )


if __name__ == "__main__":
    data_type = sys.argv[1]

    try:
        file_name = sys.argv[2]
        event = {"data_type": data_type, "file_name": file_name}
    except IndexError:
        event = {"data_type": data_type, "file_name": None}

    lambda_handler(event, None)
