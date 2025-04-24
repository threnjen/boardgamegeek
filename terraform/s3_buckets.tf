# module "aws_s3_bucket" {
#   source = "terraform-aws-modules/s3-bucket/aws"
#   bucket = "${var.S3_SCRAPER_BUCKET}_${var.ENVIRONMENT}"
#   acl    = "private"

#   control_object_ownership = true
#   object_ownership         = "ObjectWriter"

#   versioning = {
#     enabled = true
#   }
# }

import {
  to = aws_s3_bucket.example
  id = "${var.S3_SCRAPER_BUCKET}_${var.ENVIRONMENT}"
}

resource "aws_s3_bucket" "example" {
  bucket = "${var.S3_SCRAPER_BUCKET}_${var.ENVIRONMENT}"

  tags = {
    Name = "${var.S3_SCRAPER_BUCKET}_${var.ENVIRONMENT}"
  }
}