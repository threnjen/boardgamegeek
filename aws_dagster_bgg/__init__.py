from dagster import (
    Definitions,
    load_assets_from_modules,
    ConfigurableResource,
    asset,
    AssetsDefinition,
)
import os

from .assets import assets
from .resources import (
    S3Resource,
    DynamoDBResource,
    LambdaHandlerResource,
    ECSResource,
    ConfigResource,
)
from .jobs import bgg_job

scraper_assets = load_assets_from_modules([assets])

all_jobs = []

REGION = os.environ.get("TF_VAR_REGION", "us-west-2")

defs = Definitions(
    assets=[*scraper_assets],
    resources={
        "s3_resource": S3Resource(
            region_name=REGION,
        ),
        "dynamodb_resource": DynamoDBResource(
            region_name=REGION, table_name="boardgamegeek"
        ),
        "lambda_resource": LambdaHandlerResource(region_name=REGION),
        "ecs_resource": ECSResource(region_name=REGION),
        "config_resource": ConfigResource(
            region_name=REGION, bucket=os.environ.get("S3_SCRAPER_BUCKET")
        ),
    },
    jobs=[bgg_job],
)
