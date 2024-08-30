import os

from scrapy_settings import *

from config import CONFIGS

SCRAPER_CONFIG = {
    "game": {
        "bot_name": BOT_NAME_GAMES,
        "s3_location": CONFIGS["scraper_urls_raw_game"],
        "local_path": f"local_data/{CONFIGS['scraper_urls_raw_game']}",
        "save_subfolder": f"local_data/{CONFIGS['scraped_xml_raw_games']}",
    },
    "user": {
        "bot_name": BOT_NAME_USERS,
        "s3_location": CONFIGS["scraper_urls_raw_user"],
        "local_path": f"local_data/{CONFIGS['scraper_urls_raw_user']}",
        "save_subfolder": f"local_data/{CONFIGS['scraped_xml_raw_users']}",
    },
}
