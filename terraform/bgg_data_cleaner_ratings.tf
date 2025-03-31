variable "bgg_data_cleaner_ratings" {
  description = "The name of the ECS task definition for the bgg_data_cleaner_ratings"
  type        = string
  default     = "bgg_data_cleaner_ratings"
}

module "bgg_data_cleaner_ratings_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = var.bgg_data_cleaner_ratings
}

module "dev_bgg_data_cleaner_ratings_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = "dev_${var.bgg_data_cleaner_ratings}"
}

module "ecs_run_permissions_bgg_data_cleaner_ratings" {
  source               = "./modules/fargate_iam_policies"
  task_definition_name = var.bgg_data_cleaner_ratings
  region               = var.REGION
  account_id           = data.aws_caller_identity.current.account_id
}

module "bgg_data_cleaner_ratings_ecs" {
  source                 = "./modules/ecs_task_definition"
  task_definition_family = var.bgg_data_cleaner_ratings
  task_definition_name   = var.bgg_data_cleaner_ratings
  registry_name          = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.bgg_data_cleaner_ratings}:latest"
  environment            = "prod"
  env_file               = "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/boardgamegeek.env"
  task_role_arn          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_data_cleaner_ratings}_FargateTaskRole"
  execution_role_arn     = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_data_cleaner_ratings}_FargateExecutionRole"
  image                  = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.bgg_data_cleaner_ratings}:latest"
  cpu                    = "4096"
  memory                 = "24576"
  region                 = var.REGION
}

module "dev_bgg_data_cleaner_ratings_ecs" {
  source                 = "./modules/ecs_task_definition"
  task_definition_family = "dev_${var.bgg_data_cleaner_ratings}"
  task_definition_name   = "dev_${var.bgg_data_cleaner_ratings}"
  registry_name          = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/dev_${var.bgg_data_cleaner_ratings}:latest"
  environment            = "dev"
  env_file               = "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/boardgamegeek.env"
  task_role_arn          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_data_cleaner_ratings}_FargateTaskRole"
  execution_role_arn     = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_data_cleaner_ratings}_FargateExecutionRole"
  image                  = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/dev_${var.bgg_data_cleaner_ratings}:latest"
  cpu                    = "1024"
  memory                 = "8192"
  region                 = var.REGION
}

module "bgg_data_cleaner_ratings_FargateTaskRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "${var.bgg_data_cleaner_ratings}_FargateTaskRole"
}

module "bgg_data_cleaner_ratings_FargateExecutionRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "${var.bgg_data_cleaner_ratings}_FargateExecutionRole"
}

resource "aws_iam_role_policy_attachment" "S3_Access_bgg_data_cleaner_ratings_FargateExecutionRole_attach" {
  role       = module.bgg_data_cleaner_ratings_FargateExecutionRole_role.name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

resource "aws_iam_role_policy_attachment" "S3_Access_boardgamegeekbgg_data_cleaner_ratings_FargateTaskRoleattach" {
  role       = module.bgg_data_cleaner_ratings_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

resource "aws_iam_role_policy_attachment" "Cloudwatch_Put_Metricsbgg_data_cleaner_ratings_FargateTaskRoleattach" {
  role       = module.bgg_data_cleaner_ratings_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.Cloudwatch_Put_Metrics_policy.arn
}

resource "aws_iam_role_policy_attachment" "glue_boardgamegeekbgg_data_cleaner_ratings_FargateTaskRoleattach" {
  role       = module.bgg_data_cleaner_ratings_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.glue_table_access.arn
}

