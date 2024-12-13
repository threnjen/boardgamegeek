import json
import os
import sys

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

    print(terraform_state_file.keys())

    return terraform_state_file


def lambda_handler(event, context):
    """Trigger the Fargate task to process the blocks"""

    terraform_state_file = get_terraform_state_file()

    print(terraform_state_file["outputs"])

    task_definition = (
        f"dev_{TASK_DEFINITION}" if ENVIRONMENT != "prod" else TASK_DEFINITION
    )
    print(task_definition)

    ecs_client = boto3.client("ecs")

    latest_version = (
        ecs_client.describe_task_definition(taskDefinition=task_definition)
        .get("taskDefinition")
        .get("revision")
    )

    number_blocks = 10
    total_entries = 5000
    block_size = total_entries // number_blocks

    # using block_size and number_blocks, make a list of tuples of start and end indexes
    blocks = [
        (x, y)
        for x, y in zip(
            range(0, total_entries, block_size),
            range(block_size, total_entries + block_size, block_size),
        )
    ]
    print(blocks)

    if ENVIRONMENT != "prod":
        blocks = [blocks[0]]

    for block in blocks:
        start = block[0]
        end = block[1]

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
                        terraform_state_file["outputs"]["sg_ec2_ssh_access"]["value"],
                        terraform_state_file["outputs"]["shared_resources_sg"]["value"],
                    ],
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


if __name__ == "__main__":

    lambda_handler(None, None)
