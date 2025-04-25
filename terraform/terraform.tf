# Copyright (c) HashiCorp, Inc.
# SPDX-License-Identifier: MPL-2.0

terraform {

  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
  backend "s3" {
    key     = "boardgamegeek.tfstate"
    bucket  = ""
    region  = ""
    profile = ""
  }
}

provider "aws" {
  region  = var.REGION
  profile = var.AWS_PROFILE
}

data "aws_caller_identity" "current" {}


