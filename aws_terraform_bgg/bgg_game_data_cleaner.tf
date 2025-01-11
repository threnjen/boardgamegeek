variable "bgg_game_data_cleaner" {
  description = "The name of the ECS task definition for the bgg_game_data_cleaner"
  type        = string
  default     = "bgg_game_data_cleaner"
}

module "bgg_game_data_cleaner_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = var.bgg_game_data_cleaner
}

module "dev_bgg_game_data_cleaner_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = "dev_${var.bgg_game_data_cleaner}"
}

module "ecs_run_permissions_bgg_game_data_cleaner" {
  source               = "./modules/fargate_iam_policies"
  task_definition_name = var.bgg_game_data_cleaner
  region               = var.REGION
  account_id           = data.aws_caller_identity.current.account_id
}

module "bgg_game_data_cleaner_ecs" {
  source                 = "./modules/ecs_task_definition"
  task_definition_family = var.bgg_game_data_cleaner
  task_definition_name   = var.bgg_game_data_cleaner
  registry_name          = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.bgg_game_data_cleaner}:latest"
  environment            = "prod"
  env_file               = "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/boardgamegeek.env"
  task_role_arn          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_game_data_cleaner}_FargateTaskRole"
  execution_role_arn     = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_game_data_cleaner}_FargateExecutionRole"
  image                  = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.bgg_game_data_cleaner}:latest"
  cpu                    = "4096"
  memory                 = "24576"
  region                 = var.REGION
}

module "dev_bgg_game_data_cleaner_ecs" {
  source                 = "./modules/ecs_task_definition"
  task_definition_family = "dev_${var.bgg_game_data_cleaner}"
  task_definition_name   = "dev_${var.bgg_game_data_cleaner}"
  registry_name          = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/dev_${var.bgg_game_data_cleaner}:latest"
  environment            = "dev"
  env_file               = "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/boardgamegeek.env"
  task_role_arn          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_game_data_cleaner}_FargateTaskRole"
  execution_role_arn     = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_game_data_cleaner}_FargateExecutionRole"
  image                  = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/dev_${var.bgg_game_data_cleaner}:latest"
  cpu                    = "512"
  memory                 = "4096"
  region                 = var.REGION
}

module "bgg_game_data_cleaner_FargateExecutionRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "${var.bgg_game_data_cleaner}_FargateExecutionRole"
}

module "bgg_game_data_cleaner_FargateTaskRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "${var.bgg_game_data_cleaner}_FargateTaskRole"
}

resource "aws_iam_role_policy_attachment" "S3_Access_bgg_game_data_cleaner_FargateExecutionRole_attach" {
  role       = module.bgg_game_data_cleaner_FargateExecutionRole_role.name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

resource "aws_iam_role_policy_attachment" "S3_Access_boardgamegeekbgg_game_data_cleaner_FargateTaskRoleattach" {
  role       = module.bgg_game_data_cleaner_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

resource "aws_iam_role_policy_attachment" "Cloudwatch_Put_Metricsbgg_game_data_cleaner_FargateTaskRoleattach" {
  role       = module.bgg_game_data_cleaner_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.Cloudwatch_Put_Metrics_policy.arn
}

resource "aws_iam_role_policy_attachment" "glue_boardgamegeekbgg_game_data_cleaner_FargateTaskRoleattach" {
  role       = module.bgg_game_data_cleaner_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.glue_table_access.arn
}