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

variable "s3_scraper_task_bucket" {
  description = "The name of the S3 bucket to store the scraper task"
  type        = string
  default     = "boardgamegeek_scraper"
}

variable "boardgamegeek_scraper" {
  description = "The name of the ECS task definition for the boardgamegeek_scraper"
  type        = string
  default     = "boardgamegeek_scraper"
}
variable "boardgamegeek_cleaner" {
  description = "The name of the ECS task definition for the boardgamegeek_cleaner"
  type        = string
  default     = "boardgamegeek_cleaner"
}
