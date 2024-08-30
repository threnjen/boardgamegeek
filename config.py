import boto3
import os
from utils.load_save import S3Loader
from utils.read_write import JSONReader

CONFIGS = S3Loader(JSONReader()).load_data(
    bucket=os.environ.get("S3_SCRAPER_BUCKET"), filename="config.json"
)["CONFIGS"]
