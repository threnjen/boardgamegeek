import boto3
import os
import pytz
from utils.s3_file_handler import S3FileHandler
from utils.local_file_handler import LocalFileHandler
from datetime import datetime

IS_LOCAL = True if os.environ.get("IS_LOCAL", "False") == "True" else False

if LocalFileHandler().check_file_exists(file_path="config.json"):
    local_datetime = LocalFileHandler().get_last_modified(file_path="config.json")
    local_datetime = local_datetime.astimezone(pytz.utc)
    NOT_FOUND = False
else:
    print("Local config not found")
    local_datetime = datetime(1970, 1, 1).astimezone(pytz.utc)
    NOT_FOUND = True

if (
    NOT_FOUND
    or S3FileHandler().get_last_modified(file_path="config.json") > local_datetime
):
    CONFIGS = S3FileHandler().load_file(file_path="config.json")
    if IS_LOCAL:
        LocalFileHandler().save_file(file_path="config.json", data=CONFIGS)
else:
    CONFIGS = LocalFileHandler().load_file(file_path="config.json")
