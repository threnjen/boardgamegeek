from dagster import AssetSelection, define_asset_job

bgg_job = define_asset_job("bgg_job", AssetSelection.all())

user_job = define_asset_job(
    "user_job", selection=["user_scraper_urls", "scraped_user_xmls"]
)
