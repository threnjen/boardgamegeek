import json

from utils.local_file_handler import LocalFileHandler
from utils.s3_file_handler import S3FileHandler

CONFIGS = LocalFileHandler().load_file(file_path="modules/config.json")
print(CONFIGS)
S3FileHandler().save_file(file_path="modules/config.json", data=CONFIGS)
