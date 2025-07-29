# Copyright (c) HashiCorp, Inc.
# SPDX-License-Identifier: MPL-2.0

terraform {

  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
  backend "s3" {
    key     = "boardgamegeek-${var.environment}.tfstate"
    bucket  = "meeplemastery-tfstate"
    region  = "us-west-2"
    profile = "234559571171_Infrastructure_Admin"
  }
}

provider "aws" {
  region  = var.REGION
  profile = var.AWS_PROFILE
}

data "aws_caller_identity" "current" {}


