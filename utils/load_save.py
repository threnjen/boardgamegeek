import os
from abc import ABC, abstractmethod

import awswrangler as wr
import boto3

from utils.read_write import DataReader, DataWriter


class DataLoader(ABC):
    def __init__(self, reader: DataReader, folder_path: str):
        self.reader = reader
        self.folder_path = folder_path

    @abstractmethod
    def load_data(self, path: str) -> dict:
        pass


class S3Loader(DataLoader):
    S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")

    def load_data(self, filename: str) -> dict:
        key = f"{self.folder_path}/{filename}"
        print(f"Loading data from S3: {key}")
        object = (
            boto3.client("s3")
            .get_object(Bucket=self.S3_SCRAPER_BUCKET, Key=key)["Body"]
            .read()
            .decode("utf-8")
        )
        return self.reader.read_data(object)


class LocalLoader(DataLoader):
    def load_data(self, filename: str) -> dict:
        print(f"Loading data from local: {self.folder_path}/{filename}")
        with open(f"{self.folder_path}/{filename}", "rb") as f:
            file = self.reader.read_data(f.read())
        return file


class DataSaver(ABC):
    def __init__(self, writer: DataWriter, folder_path: str):
        self.writer = writer
        self.folder_path = folder_path

    @abstractmethod
    def save_data(self, data: dict, filename: str) -> None:
        pass


class S3Saver(DataSaver):
    S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")

    def save_data(self, data: dict, filename: str) -> None:
        print(f"Saving data to S3: {self.folder_path}/{filename}")
        s3_client = boto3.client("s3")
        s3_client.put_object(
            self.writer.write_data(data),
            bucket=self.S3_SCRAPER_BUCKET,
            key=f"{self.folder_path}/{filename}",
        )


class LocalSaver(DataSaver):
    def save_data(self, data: dict, filename: str) -> None:
        print(f"Saving data to local: {self.folder_path}/{filename}")
        with open(f"{self.folder_path}/{filename}", "wb") as f:
            f.write(self.writer.write_data(data))
