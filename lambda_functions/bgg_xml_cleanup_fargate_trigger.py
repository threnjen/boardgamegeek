import os
import sys
import boto3

from config import CONFIGS
from utils.s3_file_handler import S3FileHandler

ENVIRONMENT = os.environ.get("TF_VAR_RESOURCE_ENV" "dev")
S3_SCRAPER_BUCKET = os.environ.get("TF_VAR_S3_SCRAPER_BUCKET")
TASK_DEFINITION = CONFIGS["xml_cleanup_task_definition"]
TERRAFORM_STATE_BUCKET = os.environ.get("TF_VAR_BUCKET")


def lambda_handler(event, context=None):
    """Trigger the Fargate task to process the files in the S3 bucket"""

    data_type = event.get("data_type")
    print(f"Running XML cleanup task for scraper type {data_type}")

    terraform_state_file = S3FileHandler().load_tfstate(
        file_path=CONFIGS["terraform_state_file"]
    )

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
        overrides={
            "containerOverrides": [
                {
                    "name": task_definition,
                    "environment": [
                        {"name": "DATA_TYPE", "value": data_type},
                    ],
                }
            ]
        },
    )


if __name__ == "__main__":
    data_type = sys.argv[1]

    lambda_handler(event={"data_type": data_type})
