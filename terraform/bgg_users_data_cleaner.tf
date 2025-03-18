variable "bgg_data_cleaner_users" {
  description = "The name of the ECS task definition for the bgg_data_cleaner_users"
  type        = string
  default     = "bgg_data_cleaner_users"
}

module "bgg_data_cleaner_users_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = var.bgg_data_cleaner_users
}

module "dev_bgg_data_cleaner_users_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = "dev_${var.bgg_data_cleaner_users}"
}

module "ecs_run_permissions_bgg_data_cleaner_users" {
  source               = "./modules/fargate_iam_policies"
  task_definition_name = var.bgg_data_cleaner_users
  region               = var.REGION
  account_id           = data.aws_caller_identity.current.account_id
}

module "bgg_data_cleaner_users_ecs" {
  source                 = "./modules/ecs_task_definition"
  task_definition_family = var.bgg_data_cleaner_users
  task_definition_name   = var.bgg_data_cleaner_users
  registry_name          = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.bgg_data_cleaner_users}:latest"
  environment            = "prod"
  env_file               = "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/boardgamegeek.env"
  task_role_arn          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_data_cleaner_users}_FargateTaskRole"
  execution_role_arn     = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_data_cleaner_users}_FargateExecutionRole"
  image                  = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.bgg_data_cleaner_users}:latest"
  cpu                    = "4096"
  memory                 = "24576"
  region                 = var.REGION
}

module "dev_bgg_data_cleaner_users_ecs" {
  source                 = "./modules/ecs_task_definition"
  task_definition_family = "dev_${var.bgg_data_cleaner_users}"
  task_definition_name   = "dev_${var.bgg_data_cleaner_users}"
  registry_name          = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/dev_${var.bgg_data_cleaner_users}:latest"
  environment            = "dev"
  env_file               = "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/boardgamegeek.env"
  task_role_arn          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_data_cleaner_users}_FargateTaskRole"
  execution_role_arn     = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_data_cleaner_users}_FargateExecutionRole"
  image                  = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/dev_${var.bgg_data_cleaner_users}:latest"
  cpu                    = "1024"
  memory                 = "8192"
  region                 = var.REGION
}

module "bgg_data_cleaner_users_FargateTaskRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "${var.bgg_data_cleaner_users}_FargateTaskRole"
}

module "bgg_data_cleaner_users_FargateExecutionRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "${var.bgg_data_cleaner_users}_FargateExecutionRole"
}

resource "aws_iam_role_policy_attachment" "S3_Access_bgg_data_cleaner_users_FargateExecutionRole_attach" {
  role       = module.bgg_data_cleaner_users_FargateExecutionRole_role.name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

resource "aws_iam_role_policy_attachment" "S3_Access_boardgamegeekbgg_data_cleaner_users_FargateTaskRoleattach" {
  role       = module.bgg_data_cleaner_users_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

resource "aws_iam_role_policy_attachment" "Cloudwatch_Put_Metricsbgg_data_cleaner_users_FargateTaskRoleattach" {
  role       = module.bgg_data_cleaner_users_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.Cloudwatch_Put_Metrics_policy.arn
}

resource "aws_iam_role_policy_attachment" "glue_boardgamegeekbgg_data_cleaner_users_FargateTaskRoleattach" {
  role       = module.bgg_data_cleaner_users_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.glue_table_access.arn
}

module "bgg_data_cleaner_users_fargate_trigger" {
  source        = "./modules/lambda_function_direct"
  function_name = "bgg_data_cleaner_users_fargate_trigger"
  timeout       = 600
  memory_size   = 128
  role          = module.bgg_data_cleaner_users_fargate_trigger_role.arn
  handler       = "${var.bgg_data_cleaner_users}_fargate_trigger.lambda_handler"
  layers        = ["arn:aws:lambda:${var.REGION}:336392948345:layer:AWSSDKPandas-Python312:13"]
  environment   = "prod"
  description   = "Lambda function to trigger the boardgamegeek cleaner fargate task"
}


module "dev_bgg_data_cleaner_users_fargate_trigger" {
  source        = "./modules/lambda_function_direct"
  function_name = "dev_bgg_data_cleaner_users_fargate_trigger"
  timeout       = 600
  memory_size   = 128
  role          = module.bgg_data_cleaner_users_fargate_trigger_role.arn
  handler       = "${var.bgg_data_cleaner_users}_fargate_trigger.lambda_handler"
  layers        = ["arn:aws:lambda:${var.REGION}:336392948345:layer:AWSSDKPandas-Python312:13"]
  environment   = "dev"
  description   = "DEV Lambda function to trigger the boardgamegeek cleaner fargate task"
}

module "bgg_data_cleaner_users_fargate_trigger_role" {
  source    = "./modules/iam_lambda_roles"
  role_name = "bgg_data_cleaner_users_fargate_trigger_role"
}

resource "aws_iam_role_policy_attachment" "bgg_data_cleaner_users_describe_attach" {
  role       = module.bgg_data_cleaner_users_fargate_trigger_role.role_name
  policy_arn = module.bgg_data_cleaner_users_describe_task_def_policy.lambda_ecs_trigger_arn
}

resource "aws_iam_role_policy_attachment" "bgg_data_cleaner_users_s3_attach" {
  role       = module.bgg_data_cleaner_users_fargate_trigger_role.role_name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

module "bgg_data_cleaner_users_describe_task_def_policy" {
  source     = "./modules/lambda_ecs_trigger_policies"
  name       = "${var.bgg_data_cleaner_users}_lambda_ecs_trigger"
  task_name  = var.bgg_data_cleaner_users
  region     = var.REGION
  account_id = data.aws_caller_identity.current.account_id
}
