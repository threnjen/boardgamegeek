import os

ENV = os.environ.get("ENV", "dev")
S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")
JSON_URLS_PREFIX = os.environ.get("JSON_URLS_PREFIX")
SCRAPER_TASK_DEFINITION = os.environ.get("SCRAPER_TASK_DEFINITION")
