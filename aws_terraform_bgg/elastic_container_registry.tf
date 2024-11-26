

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
    module.dev_bgg_ratings_data_cleaner_ecr.ecr_repository_name
  ]
}

module "bgg_boardgame_file_retrieval_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = "bgg_boardgame_file_retrieval"
}

module "bgg_orchestrator_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = "bgg_orchestrator"
}

module "dev_bgg_orchestrator_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = "dev_bgg_orchestrator"
}

module "bgg_game_data_cleaner_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = "bgg_game_data_cleaner"
}

module "dev_bgg_game_data_cleaner_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = "dev_bgg_game_data_cleaner"
}

module "bgg_ratings_data_cleaner_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = "bgg_ratings_data_cleaner"
}

module "dev_bgg_ratings_data_cleaner_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = "dev_bgg_ratings_data_cleaner"
}

module "bgg_scraper_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = "bgg_scraper"
}

module "dev_bgg_scraper_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = "dev_bgg_scraper"
}


