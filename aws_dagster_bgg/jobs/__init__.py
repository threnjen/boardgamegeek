from dagster import define_asset_job, AssetSelection

bgg_job = define_asset_job("bgg_job", AssetSelection.all())
