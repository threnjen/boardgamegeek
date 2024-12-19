import json
import os
import sys
import time

import boto3

from config import CONFIGS
from utils.processing_functions import get_s3_keys_based_on_env

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")
TASK_DEFINITION = CONFIGS["desc_task_definition"]
TERRAFORM_STATE_BUCKET = os.environ.get("TF_VAR_BUCKET")

WORKING_DIR = (
    CONFIGS["dev_directory"] if ENVIRONMENT == "dev" else CONFIGS["prod_directory"]
)

print(TASK_DEFINITION)


def get_terraform_state_file():
    """Get the terraform state file for the VPC"""

    s3_client = boto3.client("s3")
    terraform_state_file = (
        s3_client.get_object(
            Bucket=TERRAFORM_STATE_BUCKET, Key="boardgamegeek.tfstate"
        )["Body"]
        .read()
        .decode("utf-8")
    )

    terraform_state_file = json.loads(terraform_state_file)

    return terraform_state_file


def lambda_handler(event, context):
    """Trigger the Fargate task to process the blocks

    Optional args:
    - start_block: int"""

    terraform_state_file = get_terraform_state_file()

    task_definition = TASK_DEFINITION

    print(task_definition)

    ecs_client = boto3.client("ecs")

    latest_version = (
        ecs_client.describe_task_definition(taskDefinition=task_definition)
        .get("taskDefinition")
        .get("revision")
    )

    start_block = int(event.get("start_block", "0"))
    number_blocks = 10
    total_entries = 5000
    block_size = total_entries // number_blocks

    print(start_block, number_blocks, total_entries, block_size)

    # using block_size and number_blocks, make a list of tuples of start and end indexes
    blocks = [
        (start, start + block_size)
        for start in range(start_block, start_block + total_entries, block_size)
    ]
    print(blocks)

    if ENVIRONMENT != "prod":
        blocks = [(10, 20)]

    security_groups = terraform_state_file["outputs"]["shared_resources_sg"]["value"]

    print(security_groups)

    subnets = terraform_state_file["outputs"]["public_subnets"]["value"][0]
    print(subnets)

    for block in blocks:
        start = block[0]
        end = block[1]
        print(block)

        response = ecs_client.run_task(
            taskDefinition=f"{task_definition}:{latest_version}",
            cluster="boardgamegeek",
            launchType="FARGATE",
            count=1,
            platformVersion="LATEST",
            enableECSManagedTags=False,
            networkConfiguration={
                "awsvpcConfiguration": {
                    "subnets": [subnets],
                    "securityGroups": [security_groups],
                    "assignPublicIp": "ENABLED",
                },
            },
            overrides={
                "containerOverrides": [
                    {
                        "name": task_definition,
                        "environment": [
                            {"name": "START_BLOCK", "value": str(start)},
                            {"name": "END_BLOCK", "value": str(end)},
                        ],
                    }
                ]
            },
        )
        print(response)
        print(f"Successfully launched block {block}")
        time.sleep(60)


if __name__ == "__main__":

    lambda_handler({"start_block": 1000}, None)
