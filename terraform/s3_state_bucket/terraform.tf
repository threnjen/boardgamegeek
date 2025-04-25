# Copyright (c) HashiCorp, Inc.
# SPDX-License-Identifier: MPL-2.0

terraform {

  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "aws" {
  region  = var.REGION
  profile = var.AWS_PROFILE
}

data "aws_caller_identity" "current" {}