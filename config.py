import boto3
import os
from utils.s3_file_handler import S3FileHandler


CONFIGS = S3FileHandler().load_file(file_path="config.json")["CONFIGS"]
