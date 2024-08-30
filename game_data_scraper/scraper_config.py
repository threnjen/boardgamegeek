import os

from scrapy_settings import *

from config import CONFIGS

SCRAPER_CONFIG = {
    "game": {
        "bot_name": BOT_NAME_GAMES,
        "raw_urls_directory": CONFIGS["game"]["raw_urls_directory"],
        "local_path": f"local_data/{CONFIGS['game']['raw_urls_directory']}",
        "save_subfolder": f"local_data/{CONFIGS['game']['output_xml_directory']}",
    },
    "user": {
        "bot_name": BOT_NAME_USERS,
        "raw_urls_directory": CONFIGS["user"]["raw_urls_directory"],
        "local_path": f"local_data/{CONFIGS['user']['raw_urls_directory']}",
        "save_subfolder": f"local_data/{CONFIGS['user']['output_xml_directory']}",
    },
}
