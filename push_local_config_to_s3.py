from utils.s3_file_handler import S3FileHandler
from utils.local_file_handler import LocalFileHandler

CONFIGS = LocalFileHandler().load_file(file_path="config.json")["CONFIGS"]
S3FileHandler().save_json(file_path="config.json", data=CONFIGS)
