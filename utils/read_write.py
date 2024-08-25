from abc import abstractmethod, ABC
import json
import xmltodict

class DataLoader(ABC):
    @abstractmethod
    def load_data(self, data: bytes) -> dict:
        pass

class JSONLoader(DataLoader):
    def load_data(self, data: bytes) -> dict:
        return json.loads(data)


class XMLLoader(DataLoader):
    def load_data(self, data: bytes) -> dict:
        return xmltodict.parse(data)


class DataWriter(ABC):
    @abstractmethod
    def write_data(self, data: dict) -> bytes:
        pass

class JSONWriter(DataWriter):
    def write_data(self, data: dict) -> bytes:
            return json.dumps(data)

class XMLWriter(DataWriter):
    def write_data(self, data: dict) -> bytes:
        return xmltodict.unparse(data)
