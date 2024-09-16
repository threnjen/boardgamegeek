import os
import sys

import boto3

from config import CONFIGS

ENV = os.environ.get("ENV", "dev")
S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")
SCRAPER_TASK_DEFINITION = CONFIGS["cleaner_task_definition"]


def lambda_handler(event, context):
    """Trigger the Fargate task to process the files in the S3 bucket"""

    print(f"Running Game Data Cleaner task")

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
    )


if __name__ == "__main__":

    lambda_handler(None, None)
