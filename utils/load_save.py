from abc import ABC, abstractmethod
import aws_wrangler as wr
import boto3
import os

from utils.read_write import DataLoader, DataWriter


class DataLoader(ABC):
    def __init__(self, reader: DataLoader):
        self.reader = reader

    @abstractmethod
    def load_data(self, path: str) -> dict:
        pass


class S3Loader(DataLoader):
    def load_data(self, path: str) -> dict:
        print(f"Loading data from S3: {path}")
        return self.reader.load_data(wr.s3.read_bytes(path))

class LocalLoader(DataLoader):
    def load_data(self, path: str) -> dict:
        print(f"Loading data from local: {path}")
        with open(path, "rb") as f:
            file = self.reader.load_data(f.read())
        return file

class DataSaver(ABC):
    def __init__(self, writer: DataWriter):
        self.writer = writer

    @abstractmethod
    def save_data(self, data: dict, path: str) -> None:
        pass

class S3Saver(DataSaver):
    S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")
    def save_data(self, data: dict, path: str) -> None:
        print(f"Saving data to S3: {path}")
        s3_client = boto3.client("s3")
        s3_client.put_object(self.writer.write_data(data), bucket = self.S3_SCRAPER_BUCKET, key = path)

class LocalSaver(DataSaver):
    def save_data(self, data: dict, path: str) -> None:
        print(f"Saving data to local: {path}")
        with open(path, "wb") as f:
            f.write(self.writer.write_data(data))