import json
from abc import ABC, abstractmethod
from typing import Union


class DataReader(ABC):
    @abstractmethod
    def read_data(cls, data: bytes) -> dict:
        pass


class JSONReader(DataReader):
    def read_data(cls, data: bytes) -> dict:
        return json.loads(data)


class XMLReader(DataReader):
    def read_data(cls, data: bytes) -> bytes:
        return data


class DataWriter(ABC):
    @abstractmethod
    def write_data(cls, data: dict) -> bytes:
        pass


class JSONWriter(DataWriter):
    def write_data(cls, data: Union[dict, list]) -> bytes:
        return json.dumps(data).encode("utf-8")


class XMLWriter(DataWriter):
    def write_data(cls, data: dict) -> dict:
        return data
