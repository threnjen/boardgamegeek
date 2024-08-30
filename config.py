import boto3
from utils.load_save import S3Loader
from utils.read_write import JSONReader

CONFIGS = S3Loader(JSONReader()).load_data("config.json")["CONFIGS"]
