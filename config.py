import os

from utils.local_file_handler import LocalFileHandler
from utils.s3_file_handler import S3FileHandler

IS_LOCAL = True if os.environ.get("IS_LOCAL", "True") == "True" else False
print(f"IS_LOCAL: {IS_LOCAL}")


print(f"\nChecking for local config file and evaluating for updates from S3.")

if LocalFileHandler().check_file_exists(file_path="config.json"):
    print("Loading config from local")
    CONFIGS = LocalFileHandler().load_file(file_path="config.json")

else:
    print("Loading config from S3")
    CONFIGS = S3FileHandler().load_file(file_path="config.json")

CONFIGS["s3_scraper_bucket"] = (
    f'{os.environ.get("TF_VAR_S3_SCRAPER_BUCKET")}-{os.environ.get("TF_VAR_RESOURCE_ENV")}'
)

CONFIGS["terraform_state_bucket"] = (
    f'{os.environ.get("TF_VAR_STATE_BUCKET")}-{os.environ.get("TF_VAR_RESOURCE_ENV")}'
)
