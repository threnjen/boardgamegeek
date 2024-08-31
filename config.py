import boto3
import os
from utils.s3_file_handler import S3FileHandler
from utils.local_file_handler import LocalFileHandler

IS_LOCAL = True if os.environ.get("IS_LOCAL", "False") == "True" else False

CONFIGS = S3FileHandler().load_file(file_path="config.json")["CONFIGS"]
if IS_LOCAL:
    LocalFileHandler().save_file(file_path="config.json", data=CONFIGS)