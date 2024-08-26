import os
from scrapy_settings import *

SCRAPER_CONFIG = {
    "game": {
        "bot_name": BOT_NAME_GAMES,
        "s3_location": os.environ.get("GAME_JSON_URLS_PREFIX"),
        "local_path": "local_data/scraper_urls_raw_game",
        "save_subfolder": "local_data/scraped_xml_raw_games",
    },
    "user": {
        "bot_name": BOT_NAME_USERS,
        "s3_location": os.environ.get("USER_JSON_URLS_PREFIX"),
        "local_path": "local_data/scraper_urls_raw_user",
        "save_subfolder": "local_data/scraped_xml_raw_users",
    },
}
