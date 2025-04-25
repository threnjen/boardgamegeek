variable "AWS_PROFILE" {
  description = "AWS profile to use for authentication"
  type        = string
}
variable "BUCKET" {
  description = "The name of the S3 bucket to store the Terraform state file"
  type        = string
}

variable "REGION" {
  description = "AWS region. Must be in string format like: us-west-2"
  type        = string
}

variable "ENVIRONMENT" {
  description = "Environment for the deployment, e.g., dev, prod"
  type        = string
}