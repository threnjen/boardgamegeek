import os

import boto3

from config import CONFIGS
from utils.s3_file_handler import S3FileHandler

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")
TERRAFORM_STATE_BUCKET = os.environ.get("TF_VAR_BUCKET")
TERRAFORM_STATE_PATH = CONFIGS["terraform_state_file"]

task_definition_ref = {
    "games": CONFIGS["game_cleaner_task_definition"],
    "ratings": CONFIGS["ratings_cleaner_task_definition"],
    "users": CONFIGS["user_cleaner_task_definition"],
}


def lambda_handler(event, context):
    """Trigger the Fargate task to process the files in the S3 bucket"""

    print(f"Running User Data Cleaner task")

    data_type = event.get("data_type")
    print(f"Running data cleanup task for scraper type {data_type}")

    terraform_state_file = S3FileHandler().load_tfstate(file_path=TERRAFORM_STATE_PATH)

    data_type_task_def = task_definition_ref.get(data_type)

    task_definition = (
        f"dev_{data_type_task_def}" if ENVIRONMENT != "prod" else data_type_task_def
    )
    print(task_definition)

    ecs_client = boto3.client("ecs")

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
                "subnets": terraform_state_file["outputs"]["public_subnets"]["value"],
                "securityGroups": [
                    terraform_state_file["outputs"]["sg_ec2_ssh_access"]["value"]
                ],
                "assignPublicIp": "ENABLED",
            },
        },
    )


if __name__ == "__main__":

    lambda_handler(None, None)
