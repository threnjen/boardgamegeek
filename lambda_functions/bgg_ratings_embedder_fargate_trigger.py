import os

import boto3

from config import CONFIGS
from utils.s3_file_handler import S3FileHandler

ENVIRONMENT = os.environ.get("TF_VAR_RESOURCE_ENV" "dev")
S3_SCRAPER_BUCKET = CONFIGS["s3_scraper_bucket"]
TERRAFORM_STATE_BUCKET = CONFIGS["terraform_state_bucket"]


def lambda_handler(event, context):
    """Trigger the Fargate task to process the files in the S3 bucket"""

    print(f"Running Ratings Embedder task")

    terraform_state_file = S3FileHandler().load_tfstate(
        file_path=CONFIGS["terraform_state_file"]
    )

    ecs_client = boto3.client("ecs")

    security_groups = [
        terraform_state_file["outputs"]["shared_resources_sg"]["value"],
        # terraform_state_file["outputs"]["sg_ec2_weaviate_port_access"]["value"],
    ]

    print(security_groups)

    subnets = terraform_state_file["outputs"]["public_subnets"]["value"][0]
    print(subnets)

    task_definition = f"bgg_ratings_embedder_{ENVIRONMENT}"
    print(task_definition)

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
                "subnets": [subnets],
                "securityGroups": security_groups,
                "assignPublicIp": "ENABLED",
            },
        },
    )


if __name__ == "__main__":

    lambda_handler(None, None)
