variable "bgg_data_cleaner_game" {
  description = "The name of the ECS task definition for the bgg_data_cleaner_game"
  type        = string
  default     = "bgg_data_cleaner_game"
}

module "bgg_data_cleaner_game_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = var.bgg_data_cleaner_game
}

module "ecs_run_permissions_bgg_data_cleaner_game" {
  source               = "./modules/fargate_iam_policies"
  task_definition_name = "${var.bgg_data_cleaner_game}_${var.RESOURCE_ENV}"
  region               = var.REGION
  account_id           = data.aws_caller_identity.current.account_id
  RESOURCE_ENV = var.RESOURCE_ENV
}

module "bgg_data_cleaner_game_ecs" {
  source                 = "./modules/ecs_task_definition"
  task_definition_family = "${var.bgg_data_cleaner_game}_${var.RESOURCE_ENV}"
  task_definition_name   = "${var.bgg_data_cleaner_game}_${var.RESOURCE_ENV}"
  registry_name          = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.bgg_data_cleaner_game}:latest"

  env_file               = "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}_${var.RESOURCE_ENV}/boardgamegeek.env"
  task_role_arn          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_data_cleaner_game}_FargateTaskRole"
  execution_role_arn     = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_data_cleaner_game}_FargateExecutionRole"
  image                  = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.bgg_data_cleaner_game}:latest"
  cpu                    = "4096"
  memory                 = "24576"
  region                 = var.REGION
  RESOURCE_ENV = var.RESOURCE_ENV
}

module "bgg_data_cleaner_game_FargateExecutionRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "${var.bgg_data_cleaner_game}_FargateExecutionRole"
}

module "bgg_data_cleaner_game_FargateTaskRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "${var.bgg_data_cleaner_game}_FargateTaskRole"
}


resource "aws_iam_role_policy_attachment" "S3_Access_boardgamegeekbgg_data_cleaner_game_FargateTaskRoleattach" {
  role       = module.bgg_data_cleaner_game_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

resource "aws_iam_role_policy_attachment" "Cloudwatch_Put_Metricsbgg_data_cleaner_game_FargateTaskRoleattach" {
  role       = module.bgg_data_cleaner_game_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.Cloudwatch_Put_Metrics_policy.arn
}

resource "aws_iam_role_policy_attachment" "glue_boardgamegeekbgg_data_cleaner_game_FargateTaskRoleattach" {
  role       = module.bgg_data_cleaner_game_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.glue_table_access.arn
}

