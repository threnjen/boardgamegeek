# Copyright (c) HashiCorp, Inc.
# SPDX-License-Identifier: MPL-2.0

module "aws_s3_bucket" {
  source = "terraform-aws-modules/s3-bucket/aws"
  bucket = "${var.BUCKET}-${var.RESOURCE_ENV}"
  acl    = "private"

  control_object_ownership = true
  object_ownership         = "ObjectWriter"

  versioning = {
    enabled = true
  }
}


