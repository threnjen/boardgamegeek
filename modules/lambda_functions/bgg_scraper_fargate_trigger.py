import json
import os
import sys

import boto3

from config import CONFIGS
from utils.processing_functions import get_s3_keys_based_on_env

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")
SCRAPER_TASK_DEFINITION = CONFIGS["scraper_task_definition"]
TERRAFORM_STATE_BUCKET = os.environ.get("TF_VAR_BUCKET")

WORKING_DIR = (
    CONFIGS["dev_directory"] if ENVIRONMENT == "dev" else CONFIGS["prod_directory"]
)

print(SCRAPER_TASK_DEFINITION)


def get_terraform_state_file_for_vpc():
    """Get the terraform state file for the VPC"""

    s3_client = boto3.client("s3")
    terraform_state_file = (
        s3_client.get_object(Bucket=TERRAFORM_STATE_BUCKET, Key="vpc.tfstate")["Body"]
        .read()
        .decode("utf-8")
    )

    terraform_state_file = json.loads(terraform_state_file)

    print(terraform_state_file.keys())

    return terraform_state_file


def lambda_handler(event, context):
    """Trigger the Fargate task to process the files in the S3 bucket"""

    scraper_type = event.get("scraper_type")

    print(f"Running scraper for {scraper_type}")

    terraform_state_file = get_terraform_state_file_for_vpc()

    print(terraform_state_file["outputs"])

    if not event.get("file_name"):
        file_prefixes = get_s3_keys_based_on_env(
            directory=f'{CONFIGS[scraper_type]["raw_urls_directory"]}'
        )

    else:
        file_name = event.get("file_name")
        file_prefixes = [
            f"{WORKING_DIR}{CONFIGS[scraper_type]['raw_urls_directory']}/{file_name}"
        ]

    task_definition = (
        f"dev_{SCRAPER_TASK_DEFINITION}"
        if ENVIRONMENT != "prod"
        else SCRAPER_TASK_DEFINITION
    )
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
                            {"name": "SCRAPER_TYPE", "value": scraper_type},
                        ],
                    }
                ]
            },
        )


if __name__ == "__main__":
    scraper_type = sys.argv[1]

    try:
        file_name = sys.argv[2]
        event = {"scraper_type": scraper_type, "file_name": file_name}
    except IndexError:
        event = {"scraper_type": scraper_type, "file_name": None}

    lambda_handler(event, None)
