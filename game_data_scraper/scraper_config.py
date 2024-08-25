import os
from scrapy_settings import *

SCRAPER_CONFIG = {
    "game": {
        "bot_name": BOT_NAME_GAMES,
        "s3_location": os.environ.get("GAME_JSON_URLS_PREFIX"),
        "local_path": "game_scraper_urls_raw",
        "local_subfolder": "scraped_games",
    },
    "user": {
        "bot_name": BOT_NAME_USERS,
        "s3_location": os.environ.get("USER_JSON_URLS_PREFIX"),
        "local_path": "user_scraper_urls_raw",
        "local_subfolder": "scraped_users",
    },
}
