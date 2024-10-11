# Locals block to aggregate the function names or other relevant outputs
locals {
  lambda_functions = [
    module.boardgame_scraper_fargate_trigger.function_name,
    module.boardgame_scraper_fargate_trigger_dev.function_name,
    module.bgg_generate_game_urls.function_name,
    module.bgg_generate_user_urls.function_name,
    module.boardgamegeek_cleaner_fargate_trigger.function_name,
    module.boardgamegeek_cleaner_fargate_trigger_dev.function_name
  ]
}

module "bgg_generate_game_urls" {
  source        = "./modules/lambda_function_direct"
  function_name = "bgg_generate_game_urls"
  timeout       = 900
  memory_size   = 512
  role          = module.bgg_generate_game_urls_lambda_role.arn
  handler       = "generate_game_urls_lambda.lambda_handler"
  layers        = ["arn:aws:lambda:us-west-2:336392948345:layer:AWSSDKPandas-Python312:9"]
  environment   = "prod"
}

module "bgg_generate_user_urls" {
  source        = "./modules/lambda_function_direct"
  function_name = "bgg_generate_user_urls"
  timeout       = 900
  memory_size   = 512
  role          = module.bgg_generate_user_urls_lambda_role.arn
  handler       = "bgg_generate_user_urls.lambda_handler"
  layers        = ["arn:aws:lambda:us-west-2:336392948345:layer:AWSSDKPandas-Python312:9"]
  environment   = "prod"
}

module "boardgame_scraper_fargate_trigger" {
  source        = "./modules/lambda_function_direct"
  function_name = "boardgame_scraper_fargate_trigger"
  timeout       = 600
  memory_size   = 128
  role          = module.boardgamegeek_scraper_fargate_trigger_role.arn
  handler       = "boardgame_scraper_fargate_trigger.lambda_handler"
  environment   = "prod"
}


module "boardgame_scraper_fargate_trigger_dev" {
  source        = "./modules/lambda_function_direct"
  function_name = "boardgame_scraper_fargate_trigger_dev"
  timeout       = 600
  memory_size   = 128
  role          = module.boardgamegeek_scraper_fargate_trigger_role.arn
  handler       = "boardgame_scraper_fargate_trigger.lambda_handler"
  environment   = "dev"
}

module "boardgamegeek_cleaner_fargate_trigger" {
  source        = "./modules/lambda_function_direct"
  function_name = "boardgamegeek_cleaner_fargate_trigger"
  timeout       = 600
  memory_size   = 128
  role          = module.boardgamegeek_cleaner_fargate_trigger_role.arn
  handler       = "boardgame_cleaner_fargate_trigger.lambda_handler"
  environment   = "prod"
}


module "boardgamegeek_cleaner_fargate_trigger_dev" {
  source        = "./modules/lambda_function_direct"
  function_name = "boardgamegeek_cleaner_fargate_trigger_dev"
  timeout       = 600
  memory_size   = 128
  role          = module.boardgamegeek_cleaner_fargate_trigger_role.arn
  handler       = "boardgame_cleaner_fargate_trigger.lambda_handler"
  environment   = "dev"
}



