variable "ecr_module_source" {
  description = "The source path for the ECR module"
  type        = string
  default     = "./modules/ecr"
}

variable "iam_ecs_roles_source" {
  description = "The source path for the Fargate IAM module"
  type        = string
  default     = "./modules/iam_ecs_roles"
}

variable "fargate_iam_policies_source" {
  description = "The source path for the Fargate IAM policies module"
  type        = string
  default     = "./modules/fargate_iam_policies"
}

variable "bgg_scraper" {
  description = "The name of the ECS task definition for the bgg_scraper"
  type        = string
  default     = "bgg_scraper"
}

variable "bgg_boardgame_file_retrieval" {
  description = "The name of the ECS task definition for the bgg_boardgame_file_retrieval"
  type        = string
  default     = "bgg_boardgame_file_retrieval"
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

variable "bgg_ratings_embedder" {
  description = "The name of the ECS task definition for the bgg_ratings_embedder"
  type        = string
  default     = "bgg_ratings_embedder"
}

variable "bgg_orchestrator" {
  description = "The name of the ECS task definition for the bgg_orchestrator"
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

variable "t2v-transformers" {
  description = "The name of the ECS task definition for the t2v-transformers"
  type        = string
  default     = "t2v-transformers"
}