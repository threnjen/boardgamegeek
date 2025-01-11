variable "bgg_scraper" {
  description = "The name of the ECS task definition for the bgg_scraper"
  type        = string
  default     = "bgg_scraper"
}

module "bgg_scraper_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = var.bgg_scraper
}

module "dev_bgg_scraper_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = "dev_${var.bgg_scraper}"
}

module "ecs_run_permissions_bgg_scraper" {
  source               = "./modules/fargate_iam_policies"
  task_definition_name = var.bgg_scraper
  region               = var.REGION
  account_id           = data.aws_caller_identity.current.account_id
}

module "bgg_scraper_ecs" {
  source                 = "./modules/ecs_task_definition"
  task_definition_family = var.bgg_scraper
  task_definition_name   = var.bgg_scraper
  registry_name          = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.bgg_scraper}:latest"
  environment            = "prod"
  env_file               = "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/boardgamegeek.env"
  task_role_arn          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_scraper}_FargateTaskRole"
  execution_role_arn     = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_scraper}_FargateExecutionRole"
  image                  = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.bgg_scraper}:latest"
  cpu                    = "512"
  memory                 = "4096"
  region                 = var.REGION
}

module "dev_bgg_scraper_ecs" {
  source                 = "./modules/ecs_task_definition"
  task_definition_family = "dev_${var.bgg_scraper}"
  task_definition_name   = "dev_${var.bgg_scraper}"
  registry_name          = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/dev_${var.bgg_scraper}:latest"
  environment            = "dev"
  env_file               = "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/boardgamegeek.env"
  task_role_arn          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_scraper}_FargateTaskRole"
  execution_role_arn     = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_scraper}_FargateExecutionRole"
  image                  = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/dev_${var.bgg_scraper}:latest"
  cpu                    = "256"
  memory                 = "2048"
  region                 = var.REGION
}

module "bgg_scraper_FargateExecutionRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "${var.bgg_scraper}_FargateExecutionRole"
}

module "bgg_scraper_FargateTaskRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "${var.bgg_scraper}_FargateTaskRole"
}
resource "aws_iam_role_policy_attachment" "S3_Access_bgg_scraperbgg_scraper_FargateExecutionRole" {
  role       = module.bgg_scraper_FargateExecutionRole_role.name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

resource "aws_iam_role_policy_attachment" "S3_Access_boardgamegeekbgg_scraper_FargateTaskRoleattach" {
  role       = module.bgg_scraper_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

resource "aws_iam_role_policy_attachment" "Cloudwatch_Put_Metric_bgg_scraper_FargateTaskRoleattach" {
  role       = module.bgg_scraper_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.Cloudwatch_Put_Metrics_policy.arn
}