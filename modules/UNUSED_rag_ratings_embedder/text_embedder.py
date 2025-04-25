import os
from typing import TypeVar

import pandas as pd
from pydantic import BaseModel, ConfigDict
from sentence_transformers import SentenceTransformer

from config import CONFIGS
from utils.processing_functions import load_file_local_first, save_file_local_first

# from sentence_transformers import SentenceTransformer
# from transformers import AutoTokenizer, AutoModel, BertTokenizerFast, BertModel
# import torch
# import torch.nn.functional as F


PandasDataFrame = TypeVar("pandas.core.frame.DataFrame")

sample_configs = {}


class TextEmbedderToFile(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    info_configs: dict = {}
    path: str = ""
    df: PandasDataFrame = pd.DataFrame()
    embed_column: str = "name"
    model: SentenceTransformer = SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2"
    )
    # tokenizer: BertTokenizerFast = AutoTokenizer.from_pretrained(
    #     "sentence-transformers/all-MiniLM-L6-v2"
    # )
    # model: BertModel = AutoModel.from_pretrained(
    #     "sentence-transformers/all-MiniLM-L6-v2"
    # )
    # tokenizer: BertTokenizerFast = AutoTokenizer.from_pretrained(
    #     "embedding_model_huggingface/"
    # )
    # model: BertModel = AutoModel.from_pretrained("embedding_model_huggingface/")

    def model_post_init(self, __context):

        configs = CONFIGS[self.info_configs["category"]]
        self.path = configs[self.info_configs["directory"]]
        file_name = self.info_configs["file_name"]

        self.df = load_file_local_first(path=self.path, file_name=file_name)

        if os.environ.get("TF_VAR_RESOURCE_ENV" "dev") != "prod":
            self.df = self.df[:100]

        keep_columns = self.info_configs["keep_columns"]
        self.df = self.df[keep_columns]

        self.embed_column = self.info_configs["embed_column"]

    # def mean_pooling(self, model_output, attention_mask):
    #     token_embeddings = model_output[
    #         0
    #     ]  # First element of model_output contains all token embeddings
    #     input_mask_expanded = (
    #         attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    #     )
    #     return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
    #         input_mask_expanded.sum(1), min=1e-9
    #     )

    def embed_text(self):
        sentences = list(self.df["value"].values)
        embeddings = self.model.encode(sentences)
        self.df["embedding"] = list(embeddings)

        # Tokenize sentences
        # encoded_input = self.tokenizer(
        #     sentences, padding=True, truncation=True, return_tensors="pt"
        # )

        # # Compute token embeddings
        # with torch.no_grad():
        #     model_output = self.model(**encoded_input)

        # # Perform pooling
        # sentence_embeddings = self.mean_pooling(
        #     model_output, encoded_input["attention_mask"]
        # )

        # # Normalize embeddings
        # sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)

        # print("Sentence embeddings:")
        # print(sentence_embeddings)

        # raw_embeddings = sentence_embeddings.numpy()

        # self.df["embedding"] = list(raw_embeddings)

    def save_embeddings(self):
        save_file_local_first(
            path=self.path,
            file_name="embeddings.pkl",
            data=self.df,
        )
