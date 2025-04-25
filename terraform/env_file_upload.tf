resource "aws_s3_object" "file_upload" {
  bucket = "${var.S3_SCRAPER_BUCKET}-${var.RESOURCE_ENV}"
  key    = "boardgamegeek.env"
  source = "../.env"
  depends_on = [ aws_s3_bucket.scraper_data_bucket ]
}
