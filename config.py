import boto3
import os
from utils.s3_file_handler import S3FileHandler
from utils.local_file_handler import LocalFileHandler

CONFIGS = S3FileHandler().load_file(file_path="config.json")["CONFIGS"]
LocalFileHandler().save_file(file_path="config.json", data=CONFIGS)