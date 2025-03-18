variable "function_name" {
  description = "The name of the function to trigger"
  type        = string
}

variable "account_id" {
  description = "The account ID of the AWS account"
  type        = string
}

variable "region" {
  description = "The region in which the Lambda function is deployed"
  type        = string
}