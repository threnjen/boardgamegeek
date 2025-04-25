# Copyright (c) HashiCorp, Inc.
# SPDX-License-Identifier: MPL-2.0

module "aws_s3_bucket" {
  source = "terraform-aws-modules/s3-bucket/aws"
  bucket = "${var.STATE_BUCKET}-${var.RESOURCE_ENV}"
  acl    = "private"

  control_object_ownership = true
  object_ownership         = "ObjectWriter"

  force_destroy = true

  tags = {
    Name        = "${var.STATE_BUCKET}-${var.RESOURCE_ENV}"
    Environment = var.RESOURCE_ENV
  }

  versioning = {
    enabled = true
  }
}

output "caller_identity" {
  value = data.aws_caller_identity.current
}

