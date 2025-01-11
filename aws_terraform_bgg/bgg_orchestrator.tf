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

resource "aws_iam_role_policy_attachment" "ecs_run_attach_game_cleaner_to_orchestrator" {
  role       = module.bgg_orchestrator_FargateTaskRole_role.name
  policy_arn = module.ecs_run_permissions_bgg_game_data_cleaner.arn
}

resource "aws_iam_role_policy_attachment" "ecs_run_attach_scraper_to_orchestrator" {
  role       = module.bgg_orchestrator_FargateTaskRole_role.name
  policy_arn = module.ecs_run_permissions_bgg_scraper.arn
}

resource "aws_iam_role_policy_attachment" "ecs_run_attach_ratings_cleaner_to_orchestrator" {
  role       = module.bgg_orchestrator_FargateTaskRole_role.name
  policy_arn = module.ecs_run_permissions_bgg_ratings_data_cleaner.arn
}

resource "aws_iam_role_policy_attachment" "ecs_run_attach_user_cleaner_to_orchestrator" {
  role       = module.bgg_orchestrator_FargateTaskRole_role.name
  policy_arn = module.ecs_run_permissions_bgg_users_data_cleaner.arn
}