import json
import os

import boto3

from modules.config import CONFIGS

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")
TASK_DEFINITION = CONFIGS["orchestrator_task_definition"]
TERRAFORM_STATE_BUCKET = os.environ.get("TF_VAR_BUCKET")


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

    print(f"Running BGGeek Orchestrator task")

    terraform_state_file = get_terraform_state_file_for_vpc()

    task_definition = (
        TASK_DEFINITION if ENVIRONMENT == "prod" else f"dev_{TASK_DEFINITION}"
    )
    print(task_definition)

    ecs_client = boto3.client("ecs")

    latest_version = (
        ecs_client.describe_task_definition(taskDefinition=task_definition)
        .get("taskDefinition")
        .get("revision")
    )

    subnets = terraform_state_file["outputs"]["public_subnets"]["value"]
    print(subnets)

    security_groups = [
        terraform_state_file["outputs"]["sg_ec2_ssh_access"]["value"],
        terraform_state_file["outputs"]["sg_ec2_dagster_port_access"]["value"],
    ]
    print(security_groups)

    response = ecs_client.run_task(
        taskDefinition=f"{task_definition}:{latest_version}",
        cluster="boardgamegeek",
        launchType="FARGATE",
        count=1,
        platformVersion="LATEST",
        enableECSManagedTags=False,
        networkConfiguration={
            "awsvpcConfiguration": {
                "subnets": subnets,
                "securityGroups": security_groups,
                "assignPublicIp": "ENABLED",
            },
        },
        overrides={
            "containerOverrides": [
                {
                    "name": task_definition,
                    "environment": [
                        {"name": "ASSET", "value": "all"},
                    ],
                }
            ]
        },
    )


if __name__ == "__main__":

    lambda_handler(None, None)
