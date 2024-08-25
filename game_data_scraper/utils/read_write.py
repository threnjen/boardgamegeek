from abc import abstractmethod, ABC
import json
import xmltodict

class DataReader(ABC):
    @abstractmethod
    def read_data(cls, data: bytes) -> dict:
        pass

class JSONReader(DataReader):
    def read_data(cls, data: bytes) -> dict:
        return json.loads(data)


class XMLReader(DataReader):
    def read_data(cls, data: bytes) -> dict:
        return xmltodict.parse(data)


class DataWriter(ABC):
    @abstractmethod
    def write_data(cls, data: dict) -> bytes:
        pass

class JSONWriter(DataWriter):
    def write_data(cls, data: dict) -> bytes:
        return json.dumps(data)

class XMLWriter(DataWriter):
    def write_data(cls, data: dict) -> bytes:
        return xmltodict.unparse(data)
