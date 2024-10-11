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

defs = Definitions(
    assets=[*scraper_assets],
    resources={
        "s3_resource": S3Resource(
            region_name="us-west-2",
        ),
        "dynamodb_resource": DynamoDBResource(
            region_name="us-west-2", table_name="boardgamegeek"
        ),
        "lambda_resource": LambdaHandlerResource(region_name="us-west-2"),
        "ecs_resource": ECSResource(region_name="us-west-2"),
        "config_resource": ConfigResource(
            region_name="us-west-2", bucket=os.environ.get("S3_SCRAPER_BUCKET")
        ),
    },
    jobs=[bgg_job],
)
