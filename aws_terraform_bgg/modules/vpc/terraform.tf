# Copyright (c) HashiCorp, Inc.
# SPDX-License-Identifier: MPL-2.0

terraform {

  required_providers {
    aws = {
      source  = "hashicorp/aws"
    }
  }

  backend "s3" {
    key    = "vpc.tfstate"
  }
}
