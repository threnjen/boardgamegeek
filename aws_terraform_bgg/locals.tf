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
    module.bgg_ratings_embedder.ecr_repository_name,
    module.dev_bgg_ratings_embedder.ecr_repository_name,
  ]
}

locals {
  lambda_functions = [
    module.bgg_scraper_fargate_trigger.function_name,
    module.dev_bgg_scraper_fargate_trigger.function_name,
    module.bgg_generate_game_urls.function_name,
    module.dev_bgg_generate_game_urls.function_name,
    module.bgg_generate_ratings_urls.function_name,
    module.dev_bgg_generate_ratings_urls.function_name,
    module.bgg_game_data_cleaner_fargate_trigger.function_name,
    module.dev_bgg_game_data_cleaner_fargate_trigger.function_name,
    module.bgg_orchestrator_fargate_trigger.function_name,
    module.dev_bgg_orchestrator_fargate_trigger.function_name,
    module.bgg_ratings_data_cleaner_fargate_trigger.function_name,
    module.dev_bgg_ratings_data_cleaner_fargate_trigger.function_name,
    module.bgg_generate_user_urls.function_name,
    module.dev_bgg_generate_user_urls.function_name,
    module.bgg_users_data_cleaner_fargate_trigger.function_name,
    module.dev_bgg_users_data_cleaner_fargate_trigger.function_name,
    module.rag_description_generation.function_name,
    module.dev_rag_description_generation.function_name,
    module.bgg_ratings_embedder_fargate_trigger.function_name,
    module.dev_bgg_ratings_embedder_fargate_trigger.function_name
  ]
}