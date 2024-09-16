from dagster import EnvVar, ConfigurableResource
import boto3
import json
from datetime import datetime
import pytz


class DynamoDBResource(ConfigurableResource):
    region_name: str
    table_name: str

    def get_dynamodb_client(self):
        return boto3.client("dynamodb", region_name="us-west-2")

    def get_last_modified(self, key):
        print(f"Key: {key}")
        return self.get_dynamodb_client().get_item(
            TableName=self.table_name,
            Key={
                "filename": {
                    "S": key,
                }
            },
        )["Item"]["last_modified"]["S"]

    def update_last_modified(self, key, timestamp):
        print(f"Key: {key}, Timestamp: {timestamp}")
        self.get_dynamodb_client().put_item(
            TableName=self.table_name,
            Item={"filename": {"S": key}, "last_modified": {"S": timestamp}},
        )


class LambdaHandlerResource(ConfigurableResource):
    region_name: str

    def get_lambda_handler(self):
        return boto3.client("lambda", region_name="us-west-2")

    def invoke_lambda(self, function):
        return self.get_lambda_handler().invoke(FunctionName=function)


class S3Resource(ConfigurableResource):
    region_name: str

    def get_s3_client(self):
        return boto3.client("s3", region_name=self.region_name)

    def get_last_modified(self, bucket: str, key):
        print(f"Bucket: {bucket}, Key: {key}")
        try:
            return self.get_s3_client().get_object_attributes(
                Bucket=bucket, Key=key, ObjectAttributes=["ObjectParts"]
            )["LastModified"]
        except:
            return datetime(1970, 1, 1, 0, 0, 0, 0, pytz.UTC)

    def list_file_keys(self, bucket: str, key):
        raw_files = self.get_s3_client().list_objects_v2(Bucket=bucket, Prefix=key)[
            "Contents"
        ]
        return [x["Key"] for x in raw_files]

    def load_json(self, bucket: str, key):
        print(f"Loading data from S3: {key}")
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
            print("No config file found")
            configs = S3Resource(region_name=self.region_name).load_json(
                bucket=self.bucket, key="config.json"
            )
            json.dump(configs, open("config.json", "w"))
            return configs


class ECSResource(ConfigurableResource):
    region_name: str

    def get_ecs_client(self):
        return boto3.client("ecs", region_name=self.region_name)

    def get_latest_task_revision(self, task_definition):
        return (
            self.get_ecs_client()
            .describe_task_definition(taskDefinition=task_definition)
            .get("taskDefinition")
            .get("revision")
        )

    def launch_ecs_task(self, task_definition, overrides):
        self.get_ecs_client().run_task(
            taskDefinition=f"{task_definition}:{self.get_latest_task_revision(task_definition)}",
            cluster=ConfigResource()["ecs_task_components"]["cluster"],
            launchType="FARGATE",
            count=1,
            platformVersion="LATEST",
            enableECSManagedTags=False,
            networkConfiguration={
                "awsvpcConfiguration": {
                    "subnets": ConfigResource()["ecs_task_components"]["subnets"],
                    "securityGroups": ConfigResource()["ecs_task_components"][
                        "securitygroups"
                    ],
                    "assignPublicIp": "ENABLED",
                },
            },
            overrides=overrides,
        )


# s3_resource = S3Resource(region_name="us-west-2")
# dynamodb_resource = DynamoDBResource(region_name="us-west-2")
# lambda_resource = LambdaHandlerResource(region_name="us-west-2")
