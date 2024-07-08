from typing import Optional, Union
from functools import partial
import pandas as pd
import scrapy
from datetime import datetime
from bs4 import BeautifulSoup
import re
import json
import os
from scrapy.crawler import CrawlerProcess


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


def generate_raw_urls(game_ids: list[int]):
    """Generate the raw urls for the scraper"""

    return [
        f"https://www.boardgamegeek.com/xmlapi2/thing?id={target}&stats=1&type=boardgame"
        for target in game_ids
    ]


class BGGSpider(scrapy.Spider):
    """Spider to scrape BGG for game data
    """

    def __init__(self, name: str, save_folder: str, scraper_urls_raw: list[str]):
        """
        Parameters:
        name: str
            The name of the spider
        save_folder: str
            The folder to save the data to
        scraper_urls_raw: list[str]
            The urls to scrape
        """
        self.name = name
        super().__init__()
        self.scraper_urls_raw = scraper_urls_raw
        self.save_folder = save_folder

    def start_requests(self):
        for i, url in enumerate(self.scraper_urls_raw):
            print(f"Starting URL {i}: {url}")
            save_response_with_index = partial(self._save_response, response_id=i)
            yield scrapy.Request(url=url, callback=save_response_with_index)

    def _save_response(self, response: scrapy.http.Response, response_id: int):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        os.makedirs(self.save_folder, exist_ok=True)
        filename = f"{self.save_folder}/raw_bgg_xml_{response_id}_{timestamp}.xml"
        with open(filename, "wb") as f:
            f.write(response.body)


def generate_raw_urls(game_ids: list[str], block_size: int = 500):
    """Generate the raw urls for the scraper"""
    targets = [
        game_ids[i : i + block_size] for i in range(0, len(game_ids), block_size)
    ]

    return [
        f"https://www.boardgamegeek.com/xmlapi2/thing?id={','.join(block)}&stats=1&type=boardgame"
        for block in targets
    ]


if __name__ == "__main__":
    df = pd.read_csv("read_write/boardgames_ranks.csv", low_memory=False)
    game_ids = df["id"].astype(str).to_list()
    block_size = 5

    scraper_urls_raw = generate_raw_urls(game_ids[:10], block_size)

    with open("data_dirty/scraper_urls_raw.json", "w") as convert_file:
        convert_file.write(json.dumps(scraper_urls_raw))
    process = CrawlerProcess(
        settings={
            "LOG_LEVEL": "DEBUG",
            # other Scrapy settings if needed
        }
    )

    process.crawl(
        BGGSpider,
        name="bgg_raw",
        scraper_urls_raw=scraper_urls_raw,
        save_folder="data_dirty/pulled_games",
    )
    process.start()
