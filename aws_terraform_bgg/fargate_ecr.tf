

# Locals block to aggregate the function names or other relevant outputs
locals {
  ecr_repositories = [
    module.bgg_boardgame_file_retrieval_ecr.ecr_repository_name,
    module.bgg_orchestrator_ecr.ecr_repository_name,
    module.bgg_game_data_cleaner_ecr.ecr_repository_name,
    module.dev_bgg_game_data_cleaner_ecr.ecr_repository_name,
    module.bgg_scraper_ecr.ecr_repository_name,
    module.dev_bgg_scraper_ecr.ecr_repository_name,
    module.dev_bgg_orchestrator_ecr.ecr_repository_name,
    module.bgg_ratings_data_cleaner_ecr.ecr_repository_name,
    module.dev_bgg_ratings_data_cleaner_ecr.ecr_repository_name,
    module.bgg_users_data_cleaner_ecr.ecr_repository_name,
    module.dev_bgg_users_data_cleaner_ecr.ecr_repository_name,
    module.rag_description_generation_ecr.ecr_repository_name,
    module.dev_rag_description_generation_ecr.ecr_repository_name,
    module.weaviate_rag_server_ecr.ecr_repository_name,
    module.t2v-transformers_ecr.ecr_repository_name,
    module.ratings_embedder.ecr_repository_name,
    module.dev_ratings_embedder.ecr_repository_name,
  ]
}

module "bgg_boardgame_file_retrieval_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = var.bgg_boardgame_file_retrieval
}

module "weaviate_rag_server_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = var.weaviate_rag_server
}

module "t2v-transformers_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = var.t2v-transformers
}

module "ratings_embedder" {
  source              = "./modules/ecr"
  ecr_repository_name = var.bgg_ratings_embedder
}

module "dev_ratings_embedder" {
  source              = "./modules/ecr"
  ecr_repository_name = "dev_${var.bgg_ratings_embedder}"
}

module "rag_description_generation_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = var.rag_description_generation
}

module "dev_rag_description_generation_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = "dev_${var.rag_description_generation}"
}

module "bgg_orchestrator_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = var.bgg_orchestrator
}

module "dev_bgg_orchestrator_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = "dev_${var.bgg_orchestrator}"
}

module "bgg_game_data_cleaner_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = var.bgg_game_data_cleaner
}

module "dev_bgg_game_data_cleaner_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = "dev_${var.bgg_game_data_cleaner}"
}

module "bgg_ratings_data_cleaner_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = var.bgg_ratings_data_cleaner
}

module "dev_bgg_ratings_data_cleaner_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = "dev_${var.bgg_ratings_data_cleaner}"
}

module "bgg_scraper_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = var.bgg_scraper
}

module "dev_bgg_scraper_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = "dev_${var.bgg_scraper}"
}

module "bgg_users_data_cleaner_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = var.bgg_users_data_cleaner
}

module "dev_bgg_users_data_cleaner_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = "dev_${var.bgg_users_data_cleaner}"
}

