from dagster import AssetSelection, define_asset_job

bgg_job = define_asset_job(
    "bgg_job",
    selection=[
        "boardgame_ranks_csv",
        "games_scraper_urls_raw",
        "games_scraped_xml_raw",
        "game_dfs_clean",
        "ratings_scraper_urls_raw",
        "ratings_scraped_xml_raw",
        "ratings_dfs_dirty",
    ],
)

user_job = define_asset_job(
    "user_job",
    selection=["users_scraper_urls_raw", "users_scraped_xml_raw", "user_dfs_dirty"],
)
