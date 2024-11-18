# Locals block to aggregate the function names or other relevant outputs
locals {
  lambda_functions = [
    module.bgg_scraper_fargate_trigger.function_name,
    module.dev_bgg_scraper_fargate_trigger.function_name,
    module.bgg_generate_game_urls.function_name,
    module.dev_bgg_generate_game_urls.function_name,
    module.bgg_generate_user_urls.function_name,
    module.dev_bgg_generate_user_urls.function_name,
    module.bgg_cleaner_fargate_trigger.function_name,
    module.dev_bgg_cleaner_fargate_trigger.function_name,
    module.bgg_orchestrator_fargate_trigger.function_name
  ]
}

module "bgg_generate_game_urls" {
  source        = "./modules/lambda_function_direct"
  function_name = "bgg_generate_game_urls"
  timeout       = 900
  memory_size   = 1024
  role          = module.bgg_generate_game_urls_lambda_role.arn
  handler       = "generate_game_urls_lambda.lambda_handler"
  layers        = ["arn:aws:lambda:${var.REGION}:336392948345:layer:AWSSDKPandas-Python312:13"]
  environment   = "prod"
  description  = "Lambda function to generate game urls"
}

module "dev_bgg_generate_game_urls" {
  source        = "./modules/lambda_function_direct"
  function_name = "dev_bgg_generate_game_urls"
  timeout       = 900
  memory_size   = 1024
  role          = module.bgg_generate_game_urls_lambda_role.arn
  handler       = "generate_game_urls_lambda.lambda_handler"
  layers        = ["arn:aws:lambda:${var.REGION}:336392948345:layer:AWSSDKPandas-Python312:13"]
  environment   = "dev"
  description = "DEV Lambda function to generate game urls"
}

module "bgg_generate_user_urls" {
  source        = "./modules/lambda_function_direct"
  function_name = "bgg_generate_user_urls"
  timeout       = 900
  memory_size   = 1024
  role          = module.bgg_generate_user_urls_lambda_role.arn
  handler       = "generate_user_urls_lambda.lambda_handler"
  layers        = ["arn:aws:lambda:${var.REGION}:336392948345:layer:AWSSDKPandas-Python312:13"]
  environment   = "prod"
  description = "Lambda function to generate user urls"
}

module "dev_bgg_generate_user_urls" {
  source        = "./modules/lambda_function_direct"
  function_name = "dev_bgg_generate_user_urls"
  timeout       = 900
  memory_size   = 1024
  role          = module.bgg_generate_user_urls_lambda_role.arn
  handler       = "generate_user_urls_lambda.lambda_handler"
  layers        = ["arn:aws:lambda:${var.REGION}:336392948345:layer:AWSSDKPandas-Python312:13"]
  environment   = "dev"
  description = "DEV Lambda function to generate user urls"
}

module "bgg_scraper_fargate_trigger" {
  source        = "./modules/lambda_function_direct"
  function_name = "bgg_scraper_fargate_trigger"
  timeout       = 600
  memory_size   = 128
  role          = module.bgg_scraper_fargate_trigger_role.arn
  handler       = "bgg_scraper_fargate_trigger.lambda_handler"
  layers        = ["arn:aws:lambda:${var.REGION}:336392948345:layer:AWSSDKPandas-Python312:13"]
  environment   = "prod"
  description = "Lambda function to trigger the boardgamegeek scraper fargate task"
}

module "dev_bgg_scraper_fargate_trigger" {
  source        = "./modules/lambda_function_direct"
  function_name = "dev_bgg_scraper_fargate_trigger"
  timeout       = 600
  memory_size   = 128
  role          = module.bgg_scraper_fargate_trigger_role.arn
  handler       = "bgg_scraper_fargate_trigger.lambda_handler"
  layers        = ["arn:aws:lambda:${var.REGION}:336392948345:layer:AWSSDKPandas-Python312:13"]
  environment   = "dev"
  description = "DEV Lambda function to trigger the boardgamegeek scraper fargate task"
}

module "bgg_cleaner_fargate_trigger" {
  source        = "./modules/lambda_function_direct"
  function_name = "bgg_cleaner_fargate_trigger"
  timeout       = 600
  memory_size   = 128
  role          = module.bgg_cleaner_fargate_trigger_role.arn
  handler       = "bgg_cleaner_fargate_trigger.lambda_handler"
  layers        = ["arn:aws:lambda:${var.REGION}:336392948345:layer:AWSSDKPandas-Python312:13"]
  environment   = "prod"
  description = "Lambda function to trigger the boardgamegeek cleaner fargate task"
}


module "dev_bgg_cleaner_fargate_trigger" {
  source        = "./modules/lambda_function_direct"
  function_name = "dev_bgg_cleaner_fargate_trigger"
  timeout       = 600
  memory_size   = 128
  role          = module.bgg_cleaner_fargate_trigger_role.arn
  handler       = "bgg_cleaner_fargate_trigger.lambda_handler"
  layers        = ["arn:aws:lambda:${var.REGION}:336392948345:layer:AWSSDKPandas-Python312:13"]
  environment   = "dev"
  description = "DEV Lambda function to trigger the boardgamegeek cleaner fargate task"
}

module "bgg_orchestrator_fargate_trigger" {
  source        = "./modules/lambda_function_direct"
  function_name = "bgg_orchestrator_fargate_trigger"
  timeout       = 600
  memory_size   = 128
  role          = module.bgg_orchestrator_fargate_trigger_role.arn
  handler       = "bgg_orchestrator_fargate_trigger.lambda_handler"
  layers        = ["arn:aws:lambda:${var.REGION}:336392948345:layer:AWSSDKPandas-Python312:13"]
  environment   = "prod"
  description = "Lambda function to trigger the boardgamegeek orchestrator fargate task"
}

module "dev_bgg_orchestrator_fargate_trigger" {
  source        = "./modules/lambda_function_direct"
  function_name = "dev_bgg_orchestrator_fargate_trigger"
  timeout       = 600
  memory_size   = 128
  role          = module.bgg_orchestrator_fargate_trigger_role.arn
  handler       = "bgg_orchestrator_fargate_trigger.lambda_handler"
  layers        = ["arn:aws:lambda:${var.REGION}:336392948345:layer:AWSSDKPandas-Python312:13"]
  environment   = "dev"
  description = "DEV Lambda function to trigger the boardgamegeek orchestrator fargate task"
}



