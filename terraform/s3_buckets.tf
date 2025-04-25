# module "aws_s3_bucket" {
#   source = "terraform-aws-modules/s3-bucket/aws"
#   bucket = "${var.S3_SCRAPER_BUCKET}-${var.RESOURCE_ENV}"
#   acl    = "private"

#   control_object_ownership = true
#   object_ownership         = "ObjectWriter"

#   versioning = {
#     enabled = true
#   }
# }



resource "aws_s3_bucket" "scraper_data_bucket" {
  bucket = "${var.S3_SCRAPER_BUCKET}-${var.RESOURCE_ENV}"

  tags = {
    Name = "${var.S3_SCRAPER_BUCKET}-${var.RESOURCE_ENV}"
  }
}