import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Union

import pandas as pd
import pytz

from utils.file_handler import FileHandler


class LocalFileHandler(FileHandler):

    @property
    def file_missing_exception(self) -> Exception:
        return FileNotFoundError

    def make_directory(self, directory: str):
        Path(directory).mkdir(parents=True, exist_ok=True)

    def check_file_exists(self, file_path: str) -> bool:
        return os.path.exists(file_path)

    def get_last_modified(self, file_path: str) -> datetime:
        last_modified_timestamp = datetime.fromtimestamp(os.path.getmtime(file_path))

        timezone = pytz.timezone("America/Los_Angeles")
        last_modified_timestamp = last_modified_timestamp.astimezone(timezone)

        return last_modified_timestamp.astimezone(pytz.utc)

    def get_file_path(self, file_path: str) -> str:
        return file_path

    def load_json(self, file_path: str) -> Union[dict, list]:
        with open(file_path, "r") as f:
            return json.load(f)

    def save_json(self, file_path: str, data: str):
        self.make_directory
        with open(file_path, "w") as f:
            json.dump(data, f)

    def load_jsonl(self, file_path: str) -> list[dict]:
        with open(file_path, "r") as f:
            return [json.loads(line) for line in f.readlines()]

    def save_jsonl(self, file_path: str, data: str):
        self.make_directory(Path(file_path).parent)
        jsonl = "\n".join([json.dumps(line) for line in data]).encode("utf-8")
        with open(file_path, "w") as f:
            f.write(jsonl)

    def load_xml(self, file_path: str):
        with open(file_path, "r") as f:
            return f.read()

    def save_xml(self, file_path: str, data: str):
        self.make_directory(Path(file_path).parent)
        if type(data) == str:
            data = bytes(data, "utf-8")
        with open(file_path, "wb") as f:
            f.write(data)

    def load_csv(self, file_path: str) -> pd.DataFrame:
        return pd.read_csv(file_path, low_memory=False, on_bad_lines="skip", sep="\t")

    def load_pkl(self, file_path: str) -> pd.DataFrame:
        return pd.read_pickle(file_path)

    def load_tfstate(self, file_path: str) -> dict:
        with open(file_path, "r") as f:
            return json.load(f)

    def save_csv(self, file_path: str, data: pd.DataFrame):
        self.make_directory(Path(file_path).parent)
        data.to_csv(file_path, index=False, sep="\t")

    def save_pkl(self, file_path: str, data: pd.DataFrame):
        self.make_directory(Path(file_path).parent)
        data.to_pickle(file_path)

    def delete_file(self, file_path: str):
        os.remove(file_path)

    def file_exists(self, file_path: str) -> bool:
        return os.path.exists(file_path)

    def list_files(self, directory: str) -> list[str]:
        return [file for file in os.listdir(directory)]
