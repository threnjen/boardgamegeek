variable "BUCKET" {
  description = "The name of the S3 bucket to store the Terraform state file"
  type        = string
}

variable "REGION" {
  description = "AWS region. Must be in string format like: us-west-2"
  type        = string
}

variable "MY_IP_FIRST_THREE_BLOCKS" {
  description = "Your current IP block x.x.x.x/24"
  type        = string

  validation {
    condition     = can(regex("^([0-9]{1,3}\\.){2}[0-9]{1,3}$", var.MY_IP_FIRST_THREE_BLOCKS))
    error_message = "The partial IP must be in the format x.x.x, with exactly three blocks of numbers separated by dots. On Mac, you can get your ip with 'curl -4 ifconfig.co'"
  }
}

variable "bgg_scraper" {
  description = "The name of the ECS task definition for the bgg_scraper"
  type        = string
  default     = "bgg_scraper"
}
variable "bgg_game_data_cleaner" {
  description = "The name of the ECS task definition for the bgg_game_data_cleaner"
  type        = string
  default     = "bgg_game_data_cleaner"
}

variable "bgg_ratings_data_cleaner" {
  description = "The name of the ECS task definition for the bgg_ratings_data_cleaner"
  type        = string
  default     = "bgg_ratings_data_cleaner"
}

variable "bgg_users_data_cleaner" {
  description = "The name of the ECS task definition for the bgg_users_data_cleaner"
  type        = string
  default     = "bgg_users_data_cleaner"
}

variable "boardgamegeek_orchestrator" {
  description = "The name of the ECS task definition for the boardgamegeek_orchestrator"
  type        = string
  default     = "bgg_orchestrator"
}

variable "rag_description_generation" {
  description = "The name of the ECS task definition for the rag_description_generation"
  type        = string
  default     = "rag_description_generation"
}

variable "weaviate_rag_server" {
  description = "The name of the ECS task definition for the weaviate_rag_server"
  type        = string
  default     = "weaviate_rag_server"
}

variable "sentence_transformers" {
  description = "The name of the ECS task definition for the sentence_transformers"
  type        = string
  default     = "sentence_transformers"
}

variable "GITHUB_USER_NAME" {
  description = "The name of the GitHub user"
  type        = string
}

variable "S3_SCRAPER_BUCKET" {
  description = "The name of the S3 bucket to store the scraper task"
  type        = string
}

variable "vpc_cidr_block" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr_blocks" {
  description = "Available cidr blocks for public subnets"
  type        = list(string)
  default = [
    "10.0.1.0/24",
    "10.0.2.0/24",
    "10.0.3.0/24",
    "10.0.4.0/24",
    "10.0.5.0/24",
    "10.0.6.0/24",
    "10.0.7.0/24",
    "10.0.8.0/24"
  ]
}

variable "private_subnet_cidr_blocks" {
  description = "Available cidr blocks for private subnets"
  type        = list(string)
  default = [
    "10.0.101.0/24",
    "10.0.102.0/24",
    "10.0.103.0/24",
    "10.0.104.0/24",
    "10.0.105.0/24",
    "10.0.106.0/24",
    "10.0.107.0/24",
    "10.0.108.0/24"
  ]
}

variable "public_subnet_count" {
  description = "Number of public subnets"
  type        = number
  default     = 2
}

variable "private_subnet_count" {
  description = "Number of private subnets"
  type        = number
  default     = 2
}

