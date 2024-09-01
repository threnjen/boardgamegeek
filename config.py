import boto3
import os
from utils.s3_file_handler import S3FileHandler
from utils.local_file_handler import LocalFileHandler

IS_LOCAL = True if os.environ.get("IS_LOCAL", "False") == "True" else False

# Load configurations from S3
s3_configs = S3FileHandler().load_file(file_path="config.json")["CONFIGS"]

# Try to load configurations locally, if available
try:
    local_configs = LocalFileHandler().load_file(file_path="config.json")["CONFIGS"]
except FileNotFoundError:
    local_configs = None

# Determine the final CONFIGS based on comparison between S3 and local configurations
if s3_configs != local_configs:
    CONFIGS = s3_configs
    if IS_LOCAL:
        LocalFileHandler().save_file(file_path="config.json", data=CONFIGS)
else:
    CONFIGS = local_configs
