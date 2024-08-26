import os
from config import DIRECTORY_CONFIGS
from scrapy_settings import *

SCRAPER_CONFIG = {
    "game": {
        "bot_name": BOT_NAME_GAMES,
        "s3_location": DIRECTORY_CONFIGS["scraper_urls_raw_game"],
        "local_path": f"local_data/{DIRECTORY_CONFIGS['scraper_urls_raw_game']}",
        "save_subfolder": f"local_data/{DIRECTORY_CONFIGS['scraped_xml_raw_games']}",
    },
    "user": {
        "bot_name": BOT_NAME_USERS,
        "s3_location": DIRECTORY_CONFIGS["scraper_urls_raw_user"],
        "local_path": f"local_data/{DIRECTORY_CONFIGS['scraper_urls_raw_user']}",
        "save_subfolder": f"local_data/{DIRECTORY_CONFIGS['scraped_xml_raw_users']}",
    },
}
