variable "role_name" {
  description = "The name of the IAM role"
  type        = string
}

variable "AWSLambdaBasicExecutionRole" {
  description = "The ARN of the AWSLambdaBasicExecutionRole"
  type        = string
  default     = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}