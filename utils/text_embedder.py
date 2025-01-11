import pandas as pd
import os
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel
from config import CONFIGS
from utils.processing_functions import load_file_local_first, save_file_local_first

from typing import TypeVar

PandasDataFrame = TypeVar("pandas.core.frame.DataFrame")

sample_configs = {}


class TextEmbedderToFile(BaseModel):
    info_configs: dict = {}
    path: str = ""
    df: PandasDataFrame = pd.DataFrame()
    embed_column: str = "name"
    model: SentenceTransformer = SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    def model_post_init(self, __context):

        configs = CONFIGS[self.info_configs["category"]]
        self.path = configs[self.info_configs["directory"]]
        file_name = self.info_configs["file_name"]

        self.df = load_file_local_first(path=self.path, file_name=file_name)

        if os.environ.get("ENVIRONMENT", "dev") != "prod":
            self.df = self.df[:100]

        keep_columns = self.info_configs["keep_columns"]
        self.df = self.df[keep_columns]

        self.embed_column = self.info_configs["embed_column"]

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
