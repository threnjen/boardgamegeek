resource "aws_s3_object" "file_upload" {
  bucket = var.S3_SCRAPER_BUCKET
  key    = "boardgamegeek.env"
  source = "../.env"
}
