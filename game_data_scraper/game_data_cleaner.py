import pandas as pd

pd.set_option("display.max_columns", None)
import numpy as np
from bs4 import BeautifulSoup
import requests
import regex as re
import time
import json
import os
import gc
import scrapy
import boto3
from io import StringIO, BytesIO
from lxml import etree
from datetime import datetime

# ignore warnings (gets rid of Pandas copy warnings)
import warnings

warnings.filterwarnings("ignore")

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os

def get_game_data_from_page(
    game_page: BeautifulSoup, game_id: int, find_type_str: str
) -> pd.DataFrame:
    """
    Creates a dataframe to store attributes from a specified game id.

    Parameters:
    game_page: BeautifulSoup object
        The BeautifulSoup object containing the game page.
    game_id: int
        The id of the game.
    find_type_str: str
        The type of attribute to find.

    Returns:
    pd.DataFrame
        A dataframe containing the attributes of the specified type
    """

    # find all of the things on page
    all_this_type = game_page.find_all("link", type=find_type_str)

    # make dictionary for this item
    this_dict = {"BGGId": [game_id]}

    # add this item's things to dictionary
    for item in all_this_type:
        this_dict[item["value"]] = [1]

    # return dataframe
    return pd.DataFrame(this_dict)


def get_game_mechanics(game_page: BeautifulSoup, game_id: int) -> pd.DataFrame:
    """
    Creates a dataframe to store the mechanics of a specified game id.  We create customer indicators for the
    specified mechanices.

    Parameters:
    game_page: BeautifulSoup object
        The BeautifulSoup object containing the game page.
    game_id: int
        The id of the game.

    Returns:
    pd.DataFrame
        A dataframe containing the mechanics of the specified game id
    """

    specific_mechanics = {
        "Mechanism: Legacy": "Legacy",
        "Mechanism: Tableau Building": "TableauBuilding",
    }

    # find all mechanics on page
    all_mechanics = game_page.find_all("link", type="boardgamemechanic")

    # make dictionary for this item
    mechanic = {"BGGId": [int(game_id)]}

    # add this item's mechanics to dictionary
    for item in all_mechanics:
        mechanic[item["value"]] = [1]

    # Try Tableau
    for search_name, indicator in specific_mechanics.items():
        try:
            game_page.find("link", type="boardgamefamily", value=(search_name))["value"]
            mechanic[indicator] = [1]
        except:
            continue

    return pd.DataFrame(mechanic)


def create_awards(awards_level: BeautifulSoup, game_id: int) -> pd.DataFrame:
    """Create DataFrame for Awards for a specific game id

    Inputs:
    game_page: page loaded and read with BeautifulSoup
    game_id: id for this game

    Outputs:
    dataframe"""

    # find all awards on page
    all_awards = awards_level.find_all("a", class_="ng-binding")

    # make dictionary for this item
    award = {"BGGId": [int(game_id)]}

    # add this item's awards to dictionary
    for item in all_awards:
        item = re.sub("[0-9]", "", item.text).strip(" ")
        award[item] = [1]

    return pd.DataFrame(award)

def create_thing_of_type(game_page, game_id, find_type_str):
    """Create DataFrame for things for a specific game id

    Inputs:
    game_page: page loaded and read with BeautifulSoup
    game_id: id for this game

    Outputs:
    dataframe"""

    # find all of the things on page
    all_this_type = game_page.find_all("link", type=find_type_str)

    # make dictionary for this item
    this_dict = {"BGGId": [int(game_id)]}

    # add this item's things to dictionary
    for item in all_this_type:
        this_dict[item["value"]] = [1]

    # create the dataframe
    df = pd.DataFrame(this_dict)

    # return dataframe
    return df


def create_mechanics(game_page, game_id):
    """Create DataFrame for Mechanics for a specific game id

    Inputs:
    game_page: page loaded and read with BeautifulSoup
    game_id: id for this game

    Outputs:
    dataframe"""

    # find all mechanics on page
    all_mechanics = game_page.find_all("link", type="boardgamemechanic")

    # make dictionary for this item
    mechanic = {"BGGId": [int(game_id)]}

    # add this item's mechanics to dictionary
    for item in all_mechanics:
        mechanic[item["value"]] = [1]

    # Try Tableau
    try:
        game_page.find(
            "link", type="boardgamefamily", value=("Mechanism: Tableau Building")
        )["value"]
        mechanic["TableauBuilding"] = [1]
    except:
        pass

    # Try is Legacy
    try:
        game_page.find("link", type="boardgamefamily", value=("Mechanism: Legacy"))[
            "value"
        ]
        mechanic["Legacy"] = [1]
    except:
        pass

    # append to dataframe
    mechanics = pd.DataFrame(mechanic)
    # return dataframe
    return mechanics


def create_awards(awards_level, game_id):
    """Create DataFrame for Awards for a specific game id

    Inputs:
    game_page: page loaded and read with BeautifulSoup
    game_id: id for this game

    Outputs:
    dataframe"""

    # find all awards on page
    all_awards = awards_level.find_all("a", class_="ng-binding")

    # make dictionary for this item
    award = {"BGGId": [int(game_id)]}

    # add this item's awards to dictionary
    for item in all_awards:
        item = re.sub("[0-9]", "", item.text).strip(" ")
        award[item] = [1]

    # append to dataframe
    awards = pd.DataFrame(award)

    # return dataframe
    return awards
