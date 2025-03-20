variable "bgg_orchestrator" {
  description = "The name of the ECS task definition for the bgg_orchestrator"
  type        = string
  default     = "bgg_orchestrator"
}

module "bgg_orchestrator_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = var.bgg_orchestrator
}

module "dev_bgg_orchestrator_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = "dev_${var.bgg_orchestrator}"
}

module "bgg_orchestrator_ecs" {
  source                 = "./modules/ecs_task_definition"
  task_definition_family = var.bgg_orchestrator
  task_definition_name   = var.bgg_orchestrator
  registry_name          = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.bgg_orchestrator}:latest"
  environment            = "prod"
  env_file               = "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/boardgamegeek.env"
  task_role_arn          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_orchestrator}_FargateTaskRole"
  execution_role_arn     = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_orchestrator}_FargateExecutionRole"
  image                  = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.bgg_orchestrator}:latest"
  cpu                    = "1024"
  memory                 = "4096"
  region                 = var.REGION
}

module "dev_bgg_orchestrator_ecs" {
  source                 = "./modules/ecs_task_definition"
  task_definition_family = "dev_${var.bgg_orchestrator}"
  task_definition_name   = "dev_${var.bgg_orchestrator}"
  registry_name          = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.bgg_orchestrator}:latest"
  environment            = "dev"
  env_file               = "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/boardgamegeek.env"
  task_role_arn          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_orchestrator}_FargateTaskRole"
  execution_role_arn     = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_orchestrator}_FargateExecutionRole"
  image                  = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/dev_${var.bgg_orchestrator}:latest"
  cpu                    = "1024"
  memory                 = "4096"
  region                 = var.REGION
}

module "bgg_orchestrator_FargateExecutionRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "${var.bgg_orchestrator}_FargateExecutionRole"
}

module "bgg_orchestrator_FargateTaskRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "${var.bgg_orchestrator}_FargateTaskRole"
}

resource "aws_iam_role_policy_attachment" "S3_Access_bgg_orchestrator_FargateExecutionRole_attach" {
  role       = module.bgg_orchestrator_FargateExecutionRole_role.name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

resource "aws_iam_role_policy_attachment" "S3_Access_bgg_orchestrator_FargateTaskRole_attach" {
  role       = module.bgg_orchestrator_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

resource "aws_iam_role_policy_attachment" "Cloudwatch_Put_Metrics_bgg_orchestrator_FargateTaskRole_roleattach" {
  role       = module.bgg_orchestrator_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.Cloudwatch_Put_Metrics_policy.arn
}

resource "aws_iam_role_policy_attachment" "trigger_bgg_lambda_run_attach_to_orchestrator" {
  role       = module.bgg_orchestrator_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.lambda_direct_permissions.arn
}

resource "aws_iam_role_policy_attachment" "ecs_all_to_orchestrator_dev" {
  role       = module.bgg_orchestrator_FargateTaskRole_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonECS_FullAccess"
  }



module "bgg_orchestrator_fargate_trigger" {
  source        = "./modules/lambda_function_direct"
  function_name = "bgg_orchestrator_fargate_trigger"
  timeout       = 600
  memory_size   = 128
  role          = module.bgg_orchestrator_fargate_trigger_role.arn
  handler       = "${var.bgg_orchestrator}_fargate_trigger.lambda_handler"
  layers        = ["arn:aws:lambda:${var.REGION}:336392948345:layer:AWSSDKPandas-Python312:13"]
  environment   = "prod"
  description   = "Lambda function to trigger the boardgamegeek orchestrator fargate task"
}

module "dev_bgg_orchestrator_fargate_trigger" {
  source        = "./modules/lambda_function_direct"
  function_name = "dev_bgg_orchestrator_fargate_trigger"
  timeout       = 600
  memory_size   = 128
  role          = module.bgg_orchestrator_fargate_trigger_role.arn
  handler       = "${var.bgg_orchestrator}_fargate_trigger.lambda_handler"
  layers        = ["arn:aws:lambda:${var.REGION}:336392948345:layer:AWSSDKPandas-Python312:13"]
  environment   = "dev"
  description   = "DEV Lambda function to trigger the boardgamegeek orchestrator fargate task"
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