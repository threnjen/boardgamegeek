import os
import time

import boto3

from config import CONFIGS
from utils.s3_file_handler import S3FileHandler

ENVIRONMENT = os.environ.get("TF_VAR_RESOURCE_ENV" "dev")
S3_SCRAPER_BUCKET = CONFIGS["s3_scraper_bucket"]
TASK_DEFINITION = f'{CONFIGS["desc_task_definition"]}_{ENVIRONMENT}'
TERRAFORM_STATE_BUCKET = CONFIGS["terraform_state_bucket"]

WORKING_DIR = f"data/{ENVIRONMENT}/"

print(TASK_DEFINITION)


def lambda_handler(event, context):
    """Trigger the Fargate task to process the blocks

    Optional args:
    - start_block: int"""

    terraform_state_file = S3FileHandler().load_tfstate(
        file_path=CONFIGS["terraform_state_file"]
    )

    ecs_client = boto3.client("ecs")

    latest_version = (
        ecs_client.describe_task_definition(taskDefinition=TASK_DEFINITION)
        .get("taskDefinition")
        .get("revision")
    )

    start_block = int(event.get("start_block", "0"))
    number_blocks = 30
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
        blocks = [(1000, 1010)]

    security_groups = [
        terraform_state_file["outputs"]["shared_resources_sg"]["value"],
        # terraform_state_file["outputs"]["sg_ec2_weaviate_port_access"]["value"],
    ]

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
                    "securityGroups": security_groups,
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
        time.sleep(5)


if __name__ == "__main__":

    lambda_handler({"start_block": 1000}, None)
