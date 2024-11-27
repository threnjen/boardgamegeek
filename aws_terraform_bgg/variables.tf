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

variable "GITHUB_USER_NAME" {
  description = "The name of the GitHub user"
  type        = string
}

variable "S3_SCRAPER_BUCKET" {
  description = "The name of the S3 bucket to store the scraper task"
  type        = string
}
