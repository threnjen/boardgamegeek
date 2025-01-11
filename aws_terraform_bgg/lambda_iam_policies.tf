

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
  role_name = "bgg_generate_user_urls_lambda_role"
}
resource "aws_iam_role_policy_attachment" "bgg_generate_user_urls_lambda_role" {
  role       = module.bgg_generate_user_urls_lambda_role.role_name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

module "bgg_generate_ratings_urls_lambda_role" {
  source    = "./modules/iam_lambda_roles"
  role_name = "bgg_generate_ratings_urls_lambda"
}

resource "aws_iam_role_policy_attachment" "bgg_generate_ratings_urls_lambda_attach" {
  role       = module.bgg_generate_ratings_urls_lambda_role.role_name
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

module "bgg_scraper_describe_task_def_policy" {
  source     = "./modules/lambda_ecs_trigger_policies"
  name       = "${var.bgg_scraper}_lambda_ecs_trigger"
  task_name  = var.bgg_scraper
  region     = var.REGION
  account_id = data.aws_caller_identity.current.account_id
}

module "bgg_game_data_cleaner_fargate_trigger_role" {
  source    = "./modules/iam_lambda_roles"
  role_name = "${var.bgg_game_data_cleaner}_fargate_trigger_role"
}

resource "aws_iam_role_policy_attachment" "bgg_game_data_cleaner_describe_attach" {
  role       = module.bgg_game_data_cleaner_fargate_trigger_role.role_name
  policy_arn = module.bgg_game_data_cleaner_describe_task_def_policy.lambda_ecs_trigger_arn
}

resource "aws_iam_role_policy_attachment" "bgg_game_data_cleaner_s3_attach" {
  role       = module.bgg_game_data_cleaner_fargate_trigger_role.role_name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

module "bgg_game_data_cleaner_describe_task_def_policy" {
  source     = "./modules/lambda_ecs_trigger_policies"
  name       = "${var.bgg_game_data_cleaner}_lambda_ecs_trigger"
  task_name  = var.bgg_game_data_cleaner
  region     = var.REGION
  account_id = data.aws_caller_identity.current.account_id
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

module "bgg_orchestrator_task_def_policy" {
  source     = "./modules/lambda_ecs_trigger_policies"
  name       = "${var.bgg_orchestrator}_lambda_ecs_trigger"
  task_name  = var.bgg_orchestrator
  region     = var.REGION
  account_id = data.aws_caller_identity.current.account_id
}

module "bgg_ratings_data_cleaner_fargate_trigger_role" {
  source    = "./modules/iam_lambda_roles"
  role_name = "${var.bgg_ratings_data_cleaner}_fargate_trigger_role"
}

resource "aws_iam_role_policy_attachment" "bgg_ratings_data_cleaner_describe_attach" {
  role       = module.bgg_ratings_data_cleaner_fargate_trigger_role.role_name
  policy_arn = module.bgg_ratings_data_cleaner_describe_task_def_policy.lambda_ecs_trigger_arn
}

resource "aws_iam_role_policy_attachment" "bgg_ratings_data_cleaner_s3_attach" {
  role       = module.bgg_ratings_data_cleaner_fargate_trigger_role.role_name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

module "bgg_ratings_data_cleaner_describe_task_def_policy" {
  source     = "./modules/lambda_ecs_trigger_policies"
  name       = "${var.bgg_ratings_data_cleaner}_lambda_ecs_trigger"
  task_name  = var.bgg_ratings_data_cleaner
  region     = var.REGION
  account_id = data.aws_caller_identity.current.account_id
}

module "bgg_users_data_cleaner_fargate_trigger_role" {
  source    = "./modules/iam_lambda_roles"
  role_name = "bgg_users_data_cleaner_fargate_trigger_role"
}

resource "aws_iam_role_policy_attachment" "bgg_users_data_cleaner_describe_attach" {
  role       = module.bgg_users_data_cleaner_fargate_trigger_role.role_name
  policy_arn = module.bgg_users_data_cleaner_describe_task_def_policy.lambda_ecs_trigger_arn
}

resource "aws_iam_role_policy_attachment" "bgg_users_data_cleaner_s3_attach" {
  role       = module.bgg_users_data_cleaner_fargate_trigger_role.role_name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

module "bgg_users_data_cleaner_describe_task_def_policy" {
  source     = "./modules/lambda_ecs_trigger_policies"
  name       = "${var.bgg_users_data_cleaner}_lambda_ecs_trigger"
  task_name  = var.bgg_users_data_cleaner
  region     = var.REGION
  account_id = data.aws_caller_identity.current.account_id
}

module "rag_description_generation_role" {
  source    = "./modules/iam_lambda_roles"
  role_name = "rag_description_generation_retrieval_role"
}

resource "aws_iam_role_policy_attachment" "rag_description_generation_role_describe_attach" {
  role       = module.rag_description_generation_role.role_name
  policy_arn = module.rag_description_generation_describe_task_def_policy.lambda_ecs_trigger_arn
}

resource "aws_iam_role_policy_attachment" "rag_description_generation_attach" {
  role       = module.rag_description_generation_role.role_name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

module "rag_description_generation_describe_task_def_policy" {
  source     = "./modules/lambda_ecs_trigger_policies"
  name       = "${var.rag_description_generation}_lambda_ecs_trigger"
  task_name  = var.rag_description_generation
  region     = var.REGION
  account_id = data.aws_caller_identity.current.account_id
}

module "trigger_bgg_generate_game_urls_lambda" {
  source        = "./modules/iam_lambda_run_permissions"
  function_name = module.bgg_generate_game_urls.function_name
  region        = var.REGION
  account_id    = data.aws_caller_identity.current.account_id
}

module "trigger_bgg_generate_ratings_urls_lambda" {
  source        = "./modules/iam_lambda_run_permissions"
  function_name = module.bgg_generate_ratings_urls.function_name
  region        = var.REGION
  account_id    = data.aws_caller_identity.current.account_id
}

module "bgg_ratings_embedder_fargate_trigger_role" {
  source    = "./modules/iam_lambda_roles"
  role_name = "${var.bgg_ratings_embedder}_fargate_trigger_role"
}

resource "aws_iam_role_policy_attachment" "bgg_ratings_embedder_describe_attach" {
  role       = module.bgg_ratings_embedder_fargate_trigger_role.role_name
  policy_arn = module.bgg_ratings_embedder_describe_task_def_policy.lambda_ecs_trigger_arn
}

resource "aws_iam_role_policy_attachment" "bgg_ratings_embedder_s3_attach" {
  role       = module.bgg_ratings_embedder_fargate_trigger_role.role_name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

module "bgg_ratings_embedder_describe_task_def_policy" {
  source     = "./modules/lambda_ecs_trigger_policies"
  name       = "${var.bgg_ratings_embedder}_lambda_ecs_trigger"
  task_name  = var.bgg_ratings_embedder
  region     = var.REGION
  account_id = data.aws_caller_identity.current.account_id
}

resource "aws_iam_policy" "lambda_direct_permissions" {
  name        = "lambda_run_permissions"
  description = "Policy to allow running of the Lambda functions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid = "TriggerLambdaFunction"
        Action = [
          "lambda:InvokeFunction*",
        ]
        Effect   = "Allow"
        Resource = concat([for function in local.lambda_functions : "arn:aws:lambda:${var.REGION}:${data.aws_caller_identity.current.account_id}:function:${function}"], ["${aws_lambda_function.bgg_boardgame_file_retrieval_lambda.arn}"])
      },
    ]
  })
}