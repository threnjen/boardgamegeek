

# Locals block to aggregate the function names or other relevant outputs
locals {
  ecr_repositories = [
    module.bgg_boardgame_file_retrieval_ecr.ecr_repository_name,
    module.bgg_orchestrator_ecr.ecr_repository_name,
    module.boardgamegeek_cleaner_ecr.ecr_repository_name,
    module.boardgamegeek_cleaner_dev_ecr.ecr_repository_name,
    module.boardgamegeek_scraper_ecr.ecr_repository_name,
    module.boardgamegeek_scraper_dev_ecr.ecr_repository_name
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

module "boardgamegeek_cleaner_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = "boardgamegeek_cleaner"
}

module "boardgamegeek_cleaner_dev_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = "boardgamegeek_cleaner_dev"
}

module "boardgamegeek_scraper_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = "boardgamegeek_scraper"
}

module "boardgamegeek_scraper_dev_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = "boardgamegeek_scraper_dev"
}
