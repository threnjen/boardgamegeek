
variable "bgg_data_cleaner" {
  type = string
  default = "bgg_data_cleaner"
}


module "bgg_data_cleaner_fargate_trigger" {
  source        = "./modules/lambda_function_direct"
  function_name = "bgg_data_cleaner_fargate_trigger_${var.ENVIRONMENT}"
  timeout       = 600
  memory_size   = 128
  role          = module.bgg_data_cleaner_fargate_trigger_role.arn
  handler       = "${var.bgg_data_cleaner}_fargate_trigger.lambda_handler"
  layers        = ["arn:aws:lambda:${var.REGION}:336392948345:layer:AWSSDKPandas-Python312:13"]
  environment   = "prod"
  description   = "Lambda function to trigger the boardgamegeek cleaner fargate task"
}



module "bgg_data_cleaner_fargate_trigger_role" {
  source    = "./modules/iam_lambda_roles"
  role_name = "${var.bgg_data_cleaner}_fargate_trigger_role"
}

module "bgg_data_cleaner_ratings_describe_task_def_policy" {
  source     = "./modules/lambda_ecs_trigger_policies"
  name       = "${var.bgg_data_cleaner_ratings}_lambda_ecs_trigger"
  task_name  = "${var.bgg_data_cleaner_ratings}_${var.ENVIRONMENT}"
  region     = var.REGION
  account_id = data.aws_caller_identity.current.account_id
}

resource "aws_iam_role_policy_attachment" "bgg_data_cleaner_ratings_describe_attach" {
  role       = module.bgg_data_cleaner_fargate_trigger_role.role_name
  policy_arn = module.bgg_data_cleaner_ratings_describe_task_def_policy.lambda_ecs_trigger_arn
}

module "bgg_data_cleaner_game_describe_task_def_policy" {
  source     = "./modules/lambda_ecs_trigger_policies"
  name       = "${var.bgg_data_cleaner_game}_lambda_ecs_trigger"
  task_name  = "${var.bgg_data_cleaner_game}_${var.ENVIRONMENT}"
  region     = var.REGION
  account_id = data.aws_caller_identity.current.account_id
}

resource "aws_iam_role_policy_attachment" "bgg_data_cleaner_games_describe_attach" {
  role       = module.bgg_data_cleaner_fargate_trigger_role.role_name
  policy_arn = module.bgg_data_cleaner_game_describe_task_def_policy.lambda_ecs_trigger_arn
}


module "bgg_data_cleaner_users_describe_task_def_policy" {
  source     = "./modules/lambda_ecs_trigger_policies"
  name       = "${var.bgg_data_cleaner_users}_lambda_ecs_trigger"
  task_name  = "${var.bgg_data_cleaner_users}_${var.ENVIRONMENT}"
  region     = var.REGION
  account_id = data.aws_caller_identity.current.account_id
}

resource "aws_iam_role_policy_attachment" "bgg_data_cleaner_users_describe_attach" {
  role       = module.bgg_data_cleaner_fargate_trigger_role.role_name
  policy_arn = module.bgg_data_cleaner_users_describe_task_def_policy.lambda_ecs_trigger_arn
}


resource "aws_iam_role_policy_attachment" "bgg_data_cleaner_s3_attach" {
  role       = module.bgg_data_cleaner_fargate_trigger_role.role_name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}
