import json
import os

import boto3

from config import CONFIGS

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")
TASK_DEFINITION = "bgg_ratings_embedder"
TERRAFORM_STATE_BUCKET = os.environ.get("TF_VAR_BUCKET")


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
    """Trigger the Fargate task to process the files in the S3 bucket"""

    print(f"Running Ratings Embedder task")

    terraform_state_file = get_terraform_state_file()

    task_definition = (
        f"dev_{TASK_DEFINITION}" if ENVIRONMENT != "prod" else TASK_DEFINITION
    )
    print(task_definition)

    ecs_client = boto3.client("ecs")

    security_groups = [
        terraform_state_file["outputs"]["shared_resources_sg"]["value"],
        # terraform_state_file["outputs"]["sg_ec2_weaviate_port_access"]["value"],
    ]

    print(security_groups)

    subnets = terraform_state_file["outputs"]["public_subnets"]["value"][0]
    print(subnets)

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
