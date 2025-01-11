import pandas as pd
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel
from config import CONFIGS
from utils.processing_functions import load_file_local_first, save_file_local_first

from typing import TypeVar

PandasDataFrame = TypeVar("pandas.core.frame.DataFrame")

sample_configs = {}


class TextEmbedderToFile(BaseModel):
    config_file: str = ""
    path: str = ""
    df: PandasDataFrame = pd.DataFrame()
    embed_column: str = "name"
    model: SentenceTransformer = SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    def model_post_init(self, __context):
        info_configs = load_file_local_first(file_name=self.config_file)

        configs = CONFIGS[info_configs["category"]]
        self.path = configs[info_configs["directory"]]
        file_name = info_configs["file_name"]

        self.df = load_file_local_first(path=self.path, file_name=file_name)

        keep_columns = info_configs["keep_columns"]
        self.df = self.df[keep_columns]

        self.embed_column = info_configs["embed_column"]

    def embed_text(self):
        sentences = self.df["value"].values
        embeddings = self.model.encode(sentences)
        self.df["embedding"] = list(embeddings)

    def save_embeddings(self):
        save_file_local_first(
            path=self.path,
            file_name="embeddings.pkl",
            data=self.df,
        )
