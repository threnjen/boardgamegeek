variable "bgg_users_data_cleaner" {
  description = "The name of the ECS task definition for the bgg_users_data_cleaner"
  type        = string
  default     = "bgg_users_data_cleaner"
}

module "bgg_users_data_cleaner_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = var.bgg_users_data_cleaner
}

module "dev_bgg_users_data_cleaner_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = "dev_${var.bgg_users_data_cleaner}"
}

module "ecs_run_permissions_bgg_users_data_cleaner" {
  source               = "./modules/fargate_iam_policies"
  task_definition_name = var.bgg_users_data_cleaner
  region               = var.REGION
  account_id           = data.aws_caller_identity.current.account_id
}

module "bgg_users_data_cleaner_ecs" {
  source                 = "./modules/ecs_task_definition"
  task_definition_family = var.bgg_users_data_cleaner
  task_definition_name   = var.bgg_users_data_cleaner
  registry_name          = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.bgg_users_data_cleaner}:latest"
  environment            = "prod"
  env_file               = "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/boardgamegeek.env"
  task_role_arn          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_users_data_cleaner}_FargateTaskRole"
  execution_role_arn     = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_users_data_cleaner}_FargateExecutionRole"
  image                  = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.bgg_users_data_cleaner}:latest"
  cpu                    = "4096"
  memory                 = "24576"
  region                 = var.REGION
}

module "dev_bgg_users_data_cleaner_ecs" {
  source                 = "./modules/ecs_task_definition"
  task_definition_family = "dev_${var.bgg_users_data_cleaner}"
  task_definition_name   = "dev_${var.bgg_users_data_cleaner}"
  registry_name          = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/dev_${var.bgg_users_data_cleaner}:latest"
  environment            = "dev"
  env_file               = "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/boardgamegeek.env"
  task_role_arn          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_users_data_cleaner}_FargateTaskRole"
  execution_role_arn     = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_users_data_cleaner}_FargateExecutionRole"
  image                  = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/dev_${var.bgg_users_data_cleaner}:latest"
  cpu                    = "1024"
  memory                 = "8192"
  region                 = var.REGION
}

module "bgg_users_data_cleaner_FargateTaskRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "${var.bgg_users_data_cleaner}_FargateTaskRole"
}

module "bgg_users_data_cleaner_FargateExecutionRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "${var.bgg_users_data_cleaner}_FargateExecutionRole"
}

resource "aws_iam_role_policy_attachment" "S3_Access_bgg_users_data_cleaner_FargateExecutionRole_attach" {
  role       = module.bgg_users_data_cleaner_FargateExecutionRole_role.name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

resource "aws_iam_role_policy_attachment" "S3_Access_boardgamegeekbgg_users_data_cleaner_FargateTaskRoleattach" {
  role       = module.bgg_users_data_cleaner_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

resource "aws_iam_role_policy_attachment" "Cloudwatch_Put_Metricsbgg_users_data_cleaner_FargateTaskRoleattach" {
  role       = module.bgg_users_data_cleaner_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.Cloudwatch_Put_Metrics_policy.arn
}

resource "aws_iam_role_policy_attachment" "glue_boardgamegeekbgg_users_data_cleaner_FargateTaskRoleattach" {
  role       = module.bgg_users_data_cleaner_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.glue_table_access.arn
}

module "bgg_users_data_cleaner_fargate_trigger" {
  source        = "./modules/lambda_function_direct"
  function_name = "bgg_users_data_cleaner_fargate_trigger"
  timeout       = 600
  memory_size   = 128
  role          = module.bgg_users_data_cleaner_fargate_trigger_role.arn
  handler       = "${var.bgg_users_data_cleaner}_fargate_trigger.lambda_handler"
  layers        = ["arn:aws:lambda:${var.REGION}:336392948345:layer:AWSSDKPandas-Python312:13"]
  environment   = "prod"
  description   = "Lambda function to trigger the boardgamegeek cleaner fargate task"
}


module "dev_bgg_users_data_cleaner_fargate_trigger" {
  source        = "./modules/lambda_function_direct"
  function_name = "dev_bgg_users_data_cleaner_fargate_trigger"
  timeout       = 600
  memory_size   = 128
  role          = module.bgg_users_data_cleaner_fargate_trigger_role.arn
  handler       = "${var.bgg_users_data_cleaner}_fargate_trigger.lambda_handler"
  layers        = ["arn:aws:lambda:${var.REGION}:336392948345:layer:AWSSDKPandas-Python312:13"]
  environment   = "dev"
  description   = "DEV Lambda function to trigger the boardgamegeek cleaner fargate task"
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