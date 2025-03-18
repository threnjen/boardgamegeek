# Copyright (c) HashiCorp, Inc.
# SPDX-License-Identifier: MPL-2.0

provider "aws" {
  region = var.REGION
}

module "aws_s3_bucket" {
  source = "terraform-aws-modules/s3-bucket/aws"
  bucket = var.BUCKET
  acl    = "private"

  control_object_ownership = true
  object_ownership         = "ObjectWriter"

  versioning = {
    enabled = true
  }
}


