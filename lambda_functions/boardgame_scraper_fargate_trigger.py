import boto3
import os

ENV = os.environ.get("ENV", "dev")
S3_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")
URLS_PREFIX = os.environ.get("JSON_URLS_PREFIX")
SCRAPER_TASK_DEFINITION = os.environ.get("SCRAPER_TASK_DEFINITION")


def get_filenames():

    if ENV != "prod":
        raw_files = os.listdir("data_store/local_files/scraper_urls_raw")
        file_prefixes = [x for x in raw_files if x.endswith(".json")]
    else:
        s3_client = boto3.client("s3")
        raw_files = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=URLS_PREFIX)[
            "Contents"
        ]
        file_prefixes = [x["Key"] for x in raw_files]

    print(file_prefixes)
    return file_prefixes


def lambda_handler(event, context):
    file_prefixes = get_filenames()

    task_definition = (
        f"{SCRAPER_TASK_DEFINITION}-dev" if ENV != "prod" else SCRAPER_TASK_DEFINITION
    )
    print(task_definition)

    ecs_client = boto3.client("ecs", region_name="us-west-2")

    # task_arn = (
    #     ecs_client.describe_task_definition(taskDefinition=task_definition)
    #     .get("taskDefinition")
    #     .get("taskDefinitionArn")
    # )
    # print(task_arn)

    latest_version = (
        ecs_client.describe_task_definition(taskDefinition=task_definition)
        .get("taskDefinition")
        .get("revision")
    )

    for file in file_prefixes:
        filename = file.split("/")[-1].split(".")[0]
        print(filename)
        continue

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
            overrides={
                "containerOverrides": [
                    {
                        "name": task_definition,
                        "environment": [{"name": "filename", "value": filename}],
                    }
                ]
            },
        )


if __name__ == "__main__":
    lambda_handler(None, None)
