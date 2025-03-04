import json
import logging
import os
from datetime import datetime
from functools import cache

import boto3
import pytz
from dagster import ConfigurableResource, EnvVar, get_dagster_logger

logger = get_dagster_logger()

REGION = os.environ.get("TF_VAR_REGION", "us-west-2")
TERRAFORM_STATE_BUCKET = os.environ.get("TF_VAR_BUCKET")
S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")


class DynamoDBResource(ConfigurableResource):
    region_name: str
    table_name: str

    def get_dynamodb_client(self):
        return boto3.client("dynamodb", region_name=REGION)

    def get_last_modified(self, key):
        logger.info(f"Key: {key}")
        return self.get_dynamodb_client().get_item(
            TableName=self.table_name,
            Key={
                "filename": {
                    "S": key,
                }
            },
        )["Item"]["last_modified"]["S"]

    def update_last_modified(self, key, timestamp):
        logger.info(f"Key: {key}, Timestamp: {timestamp}")
        self.get_dynamodb_client().put_item(
            TableName=self.table_name,
            Item={"filename": {"S": key}, "last_modified": {"S": timestamp}},
        )


class LambdaHandlerResource(ConfigurableResource):
    region_name: str

    def get_lambda_handler(self):
        return boto3.client("lambda", region_name=REGION)

    def invoke_lambda(self, function):
        return self.get_lambda_handler().invoke(FunctionName=function)


class S3Resource(ConfigurableResource):
    region_name: str

    def get_s3_client(self):
        return boto3.client("s3", region_name=self.region_name)

    def get_last_modified(self, bucket: str, key):
        try:
            return self.get_s3_client().get_object_attributes(
                Bucket=bucket, Key=key, ObjectAttributes=["ObjectParts"]
            )["LastModified"]
        except Exception as e:
            logger.info(f"Error: {e}")
            return datetime(1970, 1, 1, 0, 0, 0, 0, pytz.UTC)

    def list_file_keys(self, bucket: str, key):
        raw_files = self.get_s3_client().list_objects_v2(Bucket=bucket, Prefix=key)[
            "Contents"
        ]
        return [x["Key"] for x in raw_files]

    def load_json(self, bucket: str, key):
        logger.info(f"Loading data from S3: {key}")
        object = (
            self.get_s3_client()
            .get_object(Bucket=bucket, Key=key)["Body"]
            .read()
            .decode("utf-8")
        )
        return json.loads(object)


class ConfigResource(ConfigurableResource):
    region_name: str
    bucket: str

    def get_config_file(self):

        try:
            return json.loads(open("config.json"))
        except:
            logger.info("No config file found")
            configs = S3Resource(region_name=self.region_name).load_json(
                bucket=self.bucket, key="config.json"
            )
            return configs


class ECSResource(ConfigurableResource):
    region_name: str

    def get_terraform_state_file(self):
        """Get the terraform state file for the VPC"""

        return S3Resource(region_name=REGION).load_json(
            bucket=TERRAFORM_STATE_BUCKET,
            key=ConfigResource(
                region_name=REGION, bucket=S3_SCRAPER_BUCKET
            ).get_config_file()["terraform_state_file"],
        )

    def get_ecs_client(self):
        return boto3.client("ecs", region_name=self.region_name)

    def get_latest_task_revision(self, task_definition):
        return (
            self.get_ecs_client()
            .describe_task_definition(taskDefinition=task_definition)
            .get("taskDefinition")
            .get("revision")
        )

    def get_all_possible_revisions(self, task_definition: str) -> list[str]:
        return (
            self.get_ecs_client()
            .list_task_definitions(familyPrefix=task_definition, maxResults=100)
            .get("taskDefinitionArns", [])
        )

    def count_running_tasks(self, status) -> int:
        return len(
            self.get_ecs_client().list_tasks(
                cluster="boardgamegeek", desiredStatus=status
            )["taskArns"]
        )

    def launch_ecs_task(self, task_definition: str, overrides: dict = {}):

        terraform_state_file = self.get_terraform_state_file()

        logger.info(
            f"Got terraform state file. Launching ECS task for {task_definition}"
        )

        try:
            self.get_ecs_client().run_task(
                taskDefinition=f"{task_definition}:{self.get_latest_task_revision(task_definition)}",
                cluster=ConfigResource(
                    region_name=REGION, bucket=S3_SCRAPER_BUCKET
                ).get_config_file()["ecs_cluster"],
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
                            terraform_state_file["outputs"]["sg_ec2_ssh_access"][
                                "value"
                            ],
                        ],
                        "assignPublicIp": "ENABLED",
                    },
                },
                overrides=overrides,
            )
        except Exception as e:
            logger.info(f"Error: {e}")


# s3_resource = S3Resource(region_name=REGION)
# dynamodb_resource = DynamoDBResource(region_name=REGION)
# lambda_resource = LambdaHandlerResource(region_name=REGION)
