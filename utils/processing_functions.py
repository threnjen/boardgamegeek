import os
from typing import Union
from datetime import datetime

import pandas as pd

from utils.local_file_handler import LocalFileHandler
from utils.s3_file_handler import S3FileHandler

import awswrangler as wr

ENV = os.getenv("ENV", "dev")
IS_LOCAL = False if os.environ.get("IS_LOCAL", "True").lower() == "false" else True
S3_SCRAPER_BUCKET = os.getenv("S3_SCRAPER_BUCKET")

# from statistics import mean

# # NLP tools
# import spacy


# nlp = spacy.load("en_core_web_sm")
import re

# import nltk
# from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
# from nltk.tokenize import word_tokenize


def save_file_local_first(path: str, file_name: str, data: Union[pd.DataFrame, dict]):
    file_path = f"{path}/{file_name}"
    print(file_path)

    if IS_LOCAL:
        print(f"Saving {file_name} to local")
        LocalFileHandler().save_file(file_path=file_path, data=data)
    if ENV == "prod":
        print(f"Saving {file_name} to S3")
        S3FileHandler().save_file(file_path=file_path, data=data)


def load_file_local_first(path: str, file_name: str):

    file_path = f"{path}/{file_name}"
    try:
        # open from local_pile_path
        file = LocalFileHandler().load_file(file_path=file_path)
    except FileNotFoundError as e:
        print(f"Downloading {file_name} from S3")
        file = S3FileHandler().load_file(file_path=file_path)
        if IS_LOCAL:
            print(f"Saving {file_name} to local")
            LocalFileHandler().save_file(file_path=file_path, data=file)
    return file


def save_to_aws_glue(data: pd.DataFrame, table: str, database: str = "boardgamegeek"):

    data = wr.catalog.sanitize_dataframe_columns_names(data)

    # data["load_time"] = datetime.now().strftime("%Y%m%d")

    wr.s3.to_parquet(
        df=data,
        path=f"s3://{S3_SCRAPER_BUCKET}/bgg-data-lake/{database}/{table}/",
        dataset=True,
        database=database,
        table=table,
        mode="overwrite",
        # partition_cols=["load_time"],
    )


def integer_reduce(data: pd.DataFrame, columns: list[str], fill_value: int = 0):
    """
    Reduces an integer type to its smallest memory size type

    Inputs:
    data: dataframe to reduce
    columns: columns to reduce
    fill_value: fill value to use if none

    Returns:
    data: dataframe with memory reduced data types
    """
    for column in columns:
        # strip all non integers
        data[column] = data[column].replace(r"[^0-9]", "", regex=True)
        data[column] = data[column].fillna(fill_value)
        data[column] = pd.to_numeric(data[column], errors="coerce", downcast="integer")

        if (data[column].max() <= 127) & (data[column].min() >= -128):
            data[column] = data[column].astype("Int8")
        elif (data[column].max() <= 32767) & (data[column].min() >= -32768):
            data[column] = data[column].astype("Int16")
        elif (data[column].max() <= 2147483647) & (data[column].min() >= -2147483648):
            data[column] = data[column].astype("Int32")

    return data


# def text_block_processor(text):
#     """Takes a block of text. Divides block into sentences with words lemmatized.
#     Sends each sentence to word processor. Concatenates all words into one string
#     Otherwise returns string of cleaned and processed words from text block

#     ARGUMENTS:
#     block of text
#     """

#     text = str(text)
#     line = re.sub(
#         r"[^a-zA-Z\s]", "", text
#     ).lower()  # removes all special characters and numbers, and makes lower case
#     line2 = re.sub(r"\s{2}", "", line).lower()  # removes extra blocks of 2 spaces
#     tokens = nlp(line)
#     words = []
#     for token in tokens:
#         if token.is_stop == False:
#             token_preprocessed = token.lemma_
#             if token_preprocessed != "":  # only continues if returned word is not empty
#                 words.append(token_preprocessed)  # appends word to list of words
#     line = " ".join(words)

#     return line


# def fix_numbers(x):
#     """
#     Checks for numbers or strings
#     If a string, strips off the "k" and multiply by 10000
#     Sends back cleaned int
#     """

#     if type(x) is int:
#         return int(x)

#     if str.endswith(x, "k"):
#         x = str(x).strip("k")
#         new_num = int(float(x) * 1000)
#         return int(new_num)

#     else:
#         return int(x)


# def clean_ratings(id_num, game_ids):
#     """
#     Loads and cleans a raw user ratings file
#     Drops game ids not present in games file
#     Drops users with fewer than 10 ratings

#     Inputs:
#     id_num: the appendation of the file to find the path
#     game_ids: list of game ids in the games file

#     Outputs:
#     Cleaned user ratings file
#     """

#     print("\nCleaning Frame #" + str(id_num))

#     # load in raw users file according to id_num inputted
#     path = "userid/user_ratings" + str(id_num) + ".pkl"
#     users = pd.read_pickle(path)

#     # convert all datatypes to float
#     float_converted = users.astype("float")

#     # delete and clean up raw users file
#     del users
#     gc.collect()

#     # create intersection between user file and game list ids
#     float_converted.columns = float_converted.columns.astype("int32")
#     cleaned = float_converted[float_converted.columns.intersection(game_ids)]

#     # delete and clean up
#     del float_converted
#     gc.collect()

#     # make a list of users with fewer than 5 user ratings
#     sums = cleaned.count(axis=1) < 5
#     # get indices for the rows with fewer than 5 ratings
#     drop_these = sums.loc[sums == True].index
#     # drop the users with fewer than 5 ratings
#     cleaned.drop(drop_these, axis=0, inplace=True)

#     # print memory usage
#     print(cleaned.info())

#     # return cleaned file
#     return cleaned


# def create_ratings_file(start_file, end_file, game_ids):
#     """
#     Puts together dataframes from a range of files
#     Each file calls the clean_ratings function
#     Then all files in range are concatenated

#     Inputs:
#     start_file: start of file name appendation
#     end_file: end file name appendation
#     game_ids_list: list of game ids in the games file

#     Outputs:
#     Cleaned and concatenated master file

#     """

#     # make an empty dataframe
#     master_file = pd.DataFrame()

#     # for each number in the range from start to end:
#     for id_num in np.arange(start_file, end_file + 1, 1):
#         print(id_num)
#         # clean the file calling clean_ratings
#         cleaned_item = clean_ratings(id_num, game_ids)
#         # append the file to the dataframe
#         master_file = pd.concat([master_file, cleaned_item], axis=0)

#     master_file.drop_duplicates(keep="first", inplace=True)

#     # clean up
#     del cleaned_item
#     gc.collect()

#     return master_file


# def process_dataframe_ratings(x, user_ratings, raw_ratings):

#     try:
#         user_ratings[x["Username"]][x["BGGId"]] = float(x["Rating"])

#     except:
#         user_ratings[x["Username"]] = {}
#         user_ratings[x["Username"]][x["BGGId"]] = float(x["Rating"])

#     raw_ratings[x["BGGId"]].append(x["Rating"])
