from dagster import AssetSelection, define_asset_job

bgg_job = define_asset_job("bgg_job", AssetSelection.all())
