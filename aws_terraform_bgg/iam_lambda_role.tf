module "bgg_boardgame_file_retrieval_role" {
  source    = "./modules/iam_lambda_roles"
  role_name = "bgg_boardgame_file_retrieval_role"
}

resource "aws_iam_role_policy_attachment" "bgg_boardgame_file_retrieval_attach" {
  role       = module.bgg_boardgame_file_retrieval_role.role_name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

module "bgg_generate_game_urls_lambda_role" {
  source    = "./modules/iam_lambda_roles"
  role_name = "bgg_generate_game_urls_lambda_role"
}
resource "aws_iam_role_policy_attachment" "bgg_generate_game_urls_lambda_role" {
  role       = module.bgg_generate_game_urls_lambda_role.role_name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

module "bgg_generate_user_urls_lambda_role" {
  source    = "./modules/iam_lambda_roles"
  role_name = "bgg_generate_user_urls_lambda"
}

resource "aws_iam_role_policy_attachment" "bgg_generate_user_urls_lambda_attach" {
  role       = module.bgg_generate_user_urls_lambda_role.role_name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

module "bgg_scraper_fargate_trigger_role" {
  source    = "./modules/iam_lambda_roles"
  role_name = "bgg_scraper_fargate_trigger_role"
}

resource "aws_iam_role_policy_attachment" "bgg_scraper_describe_attach" {
  role       = module.bgg_scraper_fargate_trigger_role.role_name
  policy_arn = module.bgg_scraper_describe_task_def_policy.lambda_ecs_trigger_arn
}

resource "aws_iam_role_policy_attachment" "bgg_scraper_S3_attach" {
  role       = module.bgg_scraper_fargate_trigger_role.role_name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

module "bgg_game_data_cleaner_fargate_trigger_role" {
  source    = "./modules/iam_lambda_roles"
  role_name = "bgg_game_data_cleaner_fargate_trigger_role"
}

resource "aws_iam_role_policy_attachment" "bgg_game_data_cleaner_describe_attach" {
  role       = module.bgg_game_data_cleaner_fargate_trigger_role.role_name
  policy_arn = module.bgg_game_data_cleaner_describe_task_def_policy.lambda_ecs_trigger_arn
}

resource "aws_iam_role_policy_attachment" "bgg_game_data_cleaner_s3_attach" {
  role       = module.bgg_game_data_cleaner_fargate_trigger_role.role_name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

module "bgg_orchestrator_fargate_trigger_role" {
  source    = "./modules/iam_lambda_roles"
  role_name = "bgg_orchestrator_fargate_trigger_role"
}

resource "aws_iam_role_policy_attachment" "bgg_orchestrator_describe_attach" {
  role       = module.bgg_orchestrator_fargate_trigger_role.role_name
  policy_arn = module.bgg_orchestrator_task_def_policy.lambda_ecs_trigger_arn
}

resource "aws_iam_role_policy_attachment" "bgg_orchestrator_s3_attach" {
  role       = module.bgg_orchestrator_fargate_trigger_role.role_name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

module "bgg_ratings_data_cleaner_fargate_trigger_role" {
  source    = "./modules/iam_lambda_roles"
  role_name = "bgg_ratings_data_cleaner_fargate_trigger_role"
}

resource "aws_iam_role_policy_attachment" "bgg_ratings_data_cleaner_describe_attach" {
  role       = module.bgg_ratings_data_cleaner_fargate_trigger_role.role_name
  policy_arn = module.bgg_ratings_data_cleaner_describe_task_def_policy.lambda_ecs_trigger_arn
}

resource "aws_iam_role_policy_attachment" "bgg_ratings_data_cleaner_s3_attach" {
  role       = module.bgg_ratings_data_cleaner_fargate_trigger_role.role_name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}