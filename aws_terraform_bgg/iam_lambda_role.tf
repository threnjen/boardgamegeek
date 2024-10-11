module "bgg_boardgame_file_retrieval_role" {
  source    = "./modules/iam_lambda_roles"
  role_name = "bgg_boardgame_file_retrieval_role"
}

resource "aws_iam_role_policy_attachment" "bgg_boardgame_file_retrieval_attach" {
  role       = module.bgg_boardgame_file_retrieval_role.role_name
  policy_arn = aws_iam_policy.S3_Access_boardgamegeek_scraper_policy.arn
}

module "bgg_generate_game_urls_lambda_role" {
  source    = "./modules/iam_lambda_roles"
  role_name = "bgg_generate_game_urls_lambda_role"
}
resource "aws_iam_role_policy_attachment" "bgg_generate_game_urls_lambda_role" {
  role       = module.bgg_generate_game_urls_lambda_role.role_name
  policy_arn = aws_iam_policy.S3_Access_boardgamegeek_scraper_policy.arn
}

module "bgg_generate_user_urls_lambda_role" {
  source    = "./modules/iam_lambda_roles"
  role_name = "bgg_generate_user_urls_lambda"
}

resource "aws_iam_role_policy_attachment" "bgg_generate_user_urls_lambda_attach" {
  role       = module.bgg_generate_user_urls_lambda_role.role_name
  policy_arn = aws_iam_policy.S3_Access_boardgamegeek_scraper_policy.arn
}

module "boardgamegeek_scraper_fargate_trigger_role" {
  source    = "./modules/iam_lambda_roles"
  role_name = "boardgamegeek_scraper_fargate_trigger_role"
}

resource "aws_iam_role_policy_attachment" "boardgamegeek_scraper_describe_attach" {
  role       = module.boardgamegeek_scraper_fargate_trigger_role.role_name
  policy_arn = module.bgg_scraper_describe_task_def_policy.lambda_ecs_trigger_arn
}

resource "aws_iam_role_policy_attachment" "boardgamegeek_scraper_cloudwatch_attach" {
  role       = module.boardgamegeek_scraper_fargate_trigger_role.role_name
  policy_arn = module.bgg_scraper_fargate_trigger_cloudwatch_policy.cloudwatch_arn
}

resource "aws_iam_role_policy_attachment" "boardgamegeek_scraper_S3_attach" {
  role       = module.boardgamegeek_scraper_fargate_trigger_role.role_name
  policy_arn = aws_iam_policy.S3_Access_boardgamegeek_scraper_policy.arn
}

module "boardgamegeek_cleaner_fargate_trigger_role" {
  source    = "./modules/iam_lambda_roles"
  role_name = "boardgamegeek_cleaner_fargate_trigger_role"
}

resource "aws_iam_role_policy_attachment" "boardgamegeek_cleaner_cloudwatch_attach" {
  role       = module.boardgamegeek_cleaner_fargate_trigger_role.role_name
  policy_arn = module.bgg_cleaner_fargate_trigger_cloudwatch_policy.cloudwatch_arn
}

resource "aws_iam_role_policy_attachment" "boardgamegeek_cleaner_describe_attach" {
  role       = module.boardgamegeek_cleaner_fargate_trigger_role.role_name
  policy_arn = module.bgg_cleaner_describe_task_def_policy.lambda_ecs_trigger_arn
}

resource "aws_iam_role_policy_attachment" "boardgamegeek_cleaner_s3_attach" {
  role       = module.boardgamegeek_cleaner_fargate_trigger_role.role_name
  policy_arn = aws_iam_policy.S3_Access_boardgamegeek_scraper_policy.arn
}


