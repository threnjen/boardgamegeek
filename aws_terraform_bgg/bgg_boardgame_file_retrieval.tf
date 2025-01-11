variable "bgg_boardgame_file_retrieval" {
  description = "The name of the ECS task definition for the bgg_boardgame_file_retrieval"
  type        = string
  default     = "bgg_boardgame_file_retrieval"
}

module "bgg_boardgame_file_retrieval_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = var.bgg_boardgame_file_retrieval
}