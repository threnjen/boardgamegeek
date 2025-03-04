from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional, Union


class FileHandler(ABC):
    def __init__(self):
        pass

    def load_file(self, file_path: str, file_type: Optional[str] = None) -> bytes:

        if file_type is None:
            file_type = file_path.split(".")[-1]
        if file_type == "json":
            return self.load_json(file_path)
        elif file_type == "jsonl":
            return self.load_jsonl(file_path)
        elif file_type == "xml":
            return self.load_xml(file_path)
        elif file_type == "csv":
            return self.load_csv(file_path)
        elif file_type == "pkl":
            return self.load_pkl(file_path)
        elif file_type == "tfstate":
            return self.load_tfstate(file_path)
        else:
            raise ValueError("Unsupported file type")

    def save_file(self, file_path: str, data: Any, file_type: Optional[str] = None):
        if file_type is None:
            file_type = file_path.split(".")[-1]
        if file_type == "json":
            self.save_json(file_path, data)
        elif file_type == "jsonl":
            self.save_jsonl(file_path, data)
        elif file_type == "xml":
            self.save_xml(file_path, data)
        elif file_type == "csv":
            self.save_csv(file_path, data)
        elif file_type == "pkl":
            self.save_pkl(file_path, data)
        else:
            raise ValueError("Unsupported file type")

    @property
    @abstractmethod
    def file_missing_exception(self) -> Exception:
        """
        The exception to raise when a file is missing.
        """
        pass

    @abstractmethod
    def check_file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists.
        """
        pass

    @abstractmethod
    def get_file_path(self, file_path: str) -> str:
        """
        Get the file path.
        """
        pass

    @abstractmethod
    def get_last_modified(self, file_path: str) -> datetime:
        """
        Get the last modified time of the file.
        """
        pass

    @abstractmethod
    def load_json(self, file_path: str) -> Union[dict, list]:
        """
        Load a JSON file.
        """
        pass

    @abstractmethod
    def load_jsonl(self, file_path: str) -> Union[dict, list]:
        """
        Load a JSONL file.
        """
        pass

    @abstractmethod
    def load_xml(self, file_path: str) -> Union[dict, list]:
        """
        Load an XML file.
        """
        pass

    @abstractmethod
    def load_csv(self, file_path: str):
        """
        Load a CSV file.
        """
        pass

    @abstractmethod
    def load_pkl(self, file_path: str) -> Union[dict, list]:
        """
        Load a pickle file.
        """
        pass

    @abstractmethod
    def load_tfstate(self, file_path: str) -> Union[dict, list]:
        """
        Load a TFState file.
        """
        pass

    @abstractmethod
    def save_json(self, file_path: str, data: Union[dict, list]):
        """
        Save a JSON file.
        """
        pass

    @abstractmethod
    def save_jsonl(self, file_path: str, data: Union[dict, list]):
        """
        Save a JSONL file.
        """
        pass

    @abstractmethod
    def save_xml(self, file_path: str, data: Union[dict, list]):
        """
        Save an XML file.
        """
        pass

    @abstractmethod
    def save_csv(self, file_path: str, data: Union[dict, list]):
        """
        Save a CSV file.
        """
        pass

    @abstractmethod
    def save_pkl(self, file_path: str, data: Union[dict, list]):
        """
        Save a pickle file.
        """
        pass

    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists.
        """
        pass

    @abstractmethod
    def delete_file(self, file_path: str):
        """
        Delete a file.
        """
        pass

    @abstractmethod
    def list_files(self, directory: str) -> list:
        """
        List files in a directory.
        """
        pass

    @abstractmethod
    def make_directory(self, directory: str):
        """
        Make a directory.
        """
        pass
