import boto3


def lambda_handler(event, context):

    group = event.get("group")

    task_definition = "boardgamegeek-scraper-dev"

    ecs_client = boto3.client("ecs")

    task_arn = (
        ecs_client.describe_task_definition(taskDefinition=task_definition)
        .get("taskDefinition")
        .get("taskDefinitionArn")
    )

    response = ecs_client.run_task(
        taskDefinition=task_arn,
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
                    "name": "boardgamegeek-scraper",
                    "environment": [{"name": "GROUP", "value": group}],
                }
            ]
        },
    )
