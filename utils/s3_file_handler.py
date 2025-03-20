import json
import os
import pickle
from datetime import datetime
from typing import Any, Union

import awswrangler as wr
import boto3
import pandas as pd

from utils.file_handler import FileHandler

S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")
REGION_NAME = os.environ.get("TF_VAR_REGION", "us-west-2")
TERRAFORM_STATE_BUCKET = os.environ.get("TF_VAR_BUCKET")


class S3FileHandler(FileHandler):

    def __init__(self):
        self._check_s3_access()
        self.s3_client = boto3.client("s3", region_name=REGION_NAME)

    def _check_s3_access(self):
        s3_client = boto3.client("s3", region_name=REGION_NAME)
        response = s3_client.head_bucket(Bucket=S3_SCRAPER_BUCKET)

    @property
    def file_missing_exception(self) -> Exception:
        return self.s3_client.exceptions.NoSuchKey

    def check_file_exists(self, file_path: str) -> bool:
        try:
            self.s3_client.head_object(Bucket=S3_SCRAPER_BUCKET, Key=file_path)
            return True
        except self.file_missing_exception:
            return False
        except:
            return False

    def get_last_modified(self, file_path: str) -> datetime:
        obj = self.s3_client.get_object(Bucket=S3_SCRAPER_BUCKET, Key=file_path)
        return obj["LastModified"]

    def make_directory(self, directory: str):
        pass

    def get_file_path(self, file_path: str) -> str:
        return file_path

    def load_json(self, file_path: str) -> Union[dict, list]:
        obj = self.s3_client.get_object(Bucket=S3_SCRAPER_BUCKET, Key=file_path)
        return json.load(obj["Body"])

    def save_json(self, file_path: str, data: Union[dict, list]):
        self.s3_client.put_object(
            Bucket=S3_SCRAPER_BUCKET,
            Key=file_path,
            Body=json.dumps(data).encode("utf-8"),
        )

    def load_jsonl(self, file_path: str) -> list[dict]:
        obj = self.s3_client.get_object(Bucket=S3_SCRAPER_BUCKET, Key=file_path)
        return [
            json.loads(line) for line in obj["Body"].read().decode("utf-8").split("\n")
        ]

    def save_jsonl(self, file_path: str, data: str):
        self.s3_client.put_object(
            Body=json.dumps(data), Bucket=S3_SCRAPER_BUCKET, Key=file_path
        )

    def load_xml(self, file_path: str):
        obj = self.s3_client.get_object(Bucket=S3_SCRAPER_BUCKET, Key=file_path)
        return obj["Body"].read().decode("utf-8")

    def save_xml(self, file_path: str, data: Any):
        if type(data) == str:
            data = bytes(data, "utf-8")
        self.s3_client.put_object(Bucket=S3_SCRAPER_BUCKET, Key=file_path, Body=data)

    def load_csv(self, file_path: str) -> Union[dict, list]:
        obj = self.s3_client.get_object(Bucket=S3_SCRAPER_BUCKET, Key=file_path)
        return pd.read_csv(obj["Body"], low_memory=False, on_bad_lines="skip", sep="\t")

    def save_csv(self, file_path: str, data: Any):
        self.s3_client.put_object(
            Bucket=S3_SCRAPER_BUCKET,
            Key=file_path,
            Body=data.to_csv(sep="\t", index=False).encode("utf-8"),
        )

    def load_pkl(self, file_path: str) -> pd.DataFrame:
        obj = self.s3_client.get_object(Bucket=S3_SCRAPER_BUCKET, Key=file_path)[
            "Body"
        ].read()
        return pickle.loads(obj)

    def save_pkl(self, file_path: str, data: Any):
        in_memory_object = pickle.dumps(data)
        self.s3_client.put_object(
            Bucket=S3_SCRAPER_BUCKET,
            Key=file_path,
            Body=in_memory_object,
        )

    def load_tfstate(self, file_path: str) -> dict:
        terraform_state_file = (
            self.s3_client.get_object(Bucket=TERRAFORM_STATE_BUCKET, Key=file_path)[
                "Body"
            ]
            .read()
            .decode("utf-8")
        )
        return json.loads(terraform_state_file)

    def delete_file(self, file_path: str):
        self.s3_client.delete_object(Bucket=S3_SCRAPER_BUCKET, Key=file_path)

    def file_exists(self, file_path: str) -> bool:
        try:
            self.s3_client.head_object(Bucket=S3_SCRAPER_BUCKET, Key=file_path)
            return True
        except self.file_missing_exception:
            return False

    def list_files(self, directory: str) -> list[str]:

        return wr.s3.list_objects(directory)
