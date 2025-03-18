variable "task_definition" {
    description = "The name of the ECS task definition"
    type        = string
}

variable "AmazonEC2ContainerServiceRole" {
  description = "The ARN of the AmazonEC2ContainerServiceRole"
  type        = string
  default     = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceRole"
}

variable "AWSAppRunnerServicePolicyForECRAccess" {
  description = "The ARN of the AWSAppRunnerServicePolicyForECRAccess"
  type        = string
  default     = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

variable "CloudWatchFullAccessV2" {
  description = "The ARN of the CloudWatchFullAccessV2"
  type        = string
  default     = "arn:aws:iam::aws:policy/CloudWatchFullAccessV2"
}

variable "AmazonECSTaskExecutionRolePolicy" {
  description = "The ARN of the AmazonECSTaskExecutionRolePolicy"
  type        = string
  default     = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}