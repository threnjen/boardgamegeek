import os
import sys
import json
import boto3

from config import CONFIGS
from utils.s3_file_handler import S3FileHandler

ENV = os.environ.get("ENV", "dev")
S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")
SCRAPER_TASK_DEFINITION = CONFIGS["scraper_task_definition"]
TERRAFORM_STATE_BUCKET = os.environ.get("TF_VAR_BUCKET")

WORKING_DIR = CONFIGS["dev_directory"] if ENV == "dev" else CONFIGS["prod_directory"]


def get_filenames(scraper_type):
    """Get the filenames of the files to be processed by the scraper"""

    s3_client = boto3.client("s3")
    raw_files = s3_client.list_objects_v2(
        Bucket=S3_SCRAPER_BUCKET,
        Prefix=f'{WORKING_DIR}{CONFIGS[scraper_type]["raw_urls_directory"]}',
    )["Contents"]
    file_prefixes = [x["Key"] for x in raw_files]

    return file_prefixes


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

    # TO DO LATER: HAVE THIS TRIGGER OFF OF EACH FILE LANDING AND SPAWN TASKS IN PARALLEL INSTEAD OF READING THE DIRECTORY

    # file_prefixes = get_filenames(scraper_type)
    file_prefixes = S3FileHandler().list_files(
        directory=f'{WORKING_DIR}{CONFIGS[scraper_type]["raw_urls_directory"]}'
    )

    task_definition = (
        f"{SCRAPER_TASK_DEFINITION}_dev" if ENV != "prod" else SCRAPER_TASK_DEFINITION
    )
    print(task_definition)

    ecs_client = boto3.client("ecs")

    latest_version = (
        ecs_client.describe_task_definition(taskDefinition=task_definition)
        .get("taskDefinition")
        .get("revision")
    )

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

    event = {"scraper_type": scraper_type}

    lambda_handler(event, None)
