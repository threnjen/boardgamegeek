import os

from utils.local_file_handler import LocalFileHandler
from utils.s3_file_handler import S3FileHandler

IS_LOCAL = True if os.environ.get("IS_LOCAL", "True") == "True" else False
print(f"IS_LOCAL: {IS_LOCAL}")

print(f"\nChecking for local config file and evaluating for updates from S3.")

if LocalFileHandler().check_file_exists(file_path="config.json"):
    local_datetime = LocalFileHandler().get_last_modified(file_path="config.json")
    NOT_FOUND = False
else:
    print("Local config not found")
    NOT_FOUND = True
if (
    NOT_FOUND
    or S3FileHandler().get_last_modified(file_path="config.json") > local_datetime
):
    print("Loading config from S3")
    CONFIGS = S3FileHandler().load_file(file_path="config.json")
    if IS_LOCAL:
        print("Saving config to local")
        LocalFileHandler().save_file(file_path="config.json", data=CONFIGS)
else:
    print("Loading config from local")
    CONFIGS = LocalFileHandler().load_file(file_path="config.json")
