from dagster import AssetSelection, define_asset_job

bgg_job = define_asset_job("bgg_job", AssetSelection.all())

user_job = define_asset_job(
    "user_job", selection=["users_scraper_urls_raw", "users_scraped_xml_raw"]
)
