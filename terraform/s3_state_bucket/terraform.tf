# Copyright (c) HashiCorp, Inc.
# SPDX-License-Identifier: MPL-2.0

terraform {

  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
  # backend "local" {}
  backend "s3" {
    bucket  = ""
    key     = ""
    region  = ""
    profile = ""
  }
}

provider "aws" {
  region  = var.REGION
  profile = var.AWS_PROFILE
}
