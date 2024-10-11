resource "aws_ecs_cluster" "boardgamegeek" {
  name = "boardgamegeek"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

module "boardgamegeek_cleaner_ecs" {
  source                 = "./modules/ecs_task_definition"
  task_definition_family = var.boardgamegeek_cleaner
  task_definition_name   = var.boardgamegeek_cleaner
  registry_name          = "${data.aws_caller_identity.current.account_id}.dkr.ecr.us-west-2.amazonaws.com/${var.boardgamegeek_cleaner}:latest"
  environment            = "prod"
  env_file               = "arn:aws:s3:::${var.s3_scraper_task_bucket}/${var.boardgamegeek_cleaner}.env"
  task_role_arn          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.boardgamegeek_cleaner}_FargateTaskRole"
  execution_role_arn     = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.boardgamegeek_cleaner}_FargateExecutionRole"
  image                  = "${data.aws_caller_identity.current.account_id}.dkr.ecr.us-west-2.amazonaws.com/${var.boardgamegeek_cleaner}:latest"
  cpu                    = "2048"
  memory                 = "16384"
  region                 = var.REGION
}

module "boardgamegeek_cleaner_dev_ecs" {
  source                 = "./modules/ecs_task_definition"
  task_definition_family = "${var.boardgamegeek_cleaner}_dev"
  task_definition_name   = "${var.boardgamegeek_cleaner}_dev"
  registry_name          = "${data.aws_caller_identity.current.account_id}.dkr.ecr.us-west-2.amazonaws.com/${var.boardgamegeek_cleaner}_dev:latest"
  environment            = "dev"
  env_file               = "arn:aws:s3:::${var.s3_scraper_task_bucket}/${var.boardgamegeek_cleaner}.env"
  task_role_arn          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.boardgamegeek_cleaner}_FargateTaskRole"
  execution_role_arn     = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.boardgamegeek_cleaner}_FargateExecutionRole"
  image                  = "${data.aws_caller_identity.current.account_id}.dkr.ecr.us-west-2.amazonaws.com/${var.boardgamegeek_cleaner}_dev:latest"
  cpu                    = "2048"
  memory                 = "16384"
  region                 = var.REGION
}


module "boardgamegeek_scraper_ecs" {
  source                 = "./modules/ecs_task_definition"
  task_definition_family = var.boardgamegeek_scraper
  task_definition_name   = var.boardgamegeek_scraper
  registry_name          = "${data.aws_caller_identity.current.account_id}.dkr.ecr.us-west-2.amazonaws.com/${var.boardgamegeek_scraper}:latest"
  environment            = "prod"
  env_file               = "arn:aws:s3:::${var.s3_scraper_task_bucket}/${var.boardgamegeek_scraper}.env"
  task_role_arn          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.boardgamegeek_scraper}_FargateTaskRole"
  execution_role_arn     = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.boardgamegeek_scraper}_FargateExecutionRole"
  image                  = "${data.aws_caller_identity.current.account_id}.dkr.ecr.us-west-2.amazonaws.com/${var.boardgamegeek_scraper}:latest"
  cpu                    = "256"
  memory                 = "2048"
  region                 = var.REGION
}

module "boardgamegeek_scraper_dev_ecs" {
  source                 = "./modules/ecs_task_definition"
  task_definition_family = "${var.boardgamegeek_scraper}_dev"
  task_definition_name   = "${var.boardgamegeek_scraper}_dev"
  registry_name          = "${data.aws_caller_identity.current.account_id}.dkr.ecr.us-west-2.amazonaws.com/${var.boardgamegeek_scraper}:latest"
  environment            = "prod"
  env_file               = "arn:aws:s3:::${var.s3_scraper_task_bucket}/${var.boardgamegeek_scraper}.env"
  task_role_arn          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.boardgamegeek_scraper}_FargateTaskRole"
  execution_role_arn     = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.boardgamegeek_scraper}_FargateExecutionRole"
  image                  = "${data.aws_caller_identity.current.account_id}.dkr.ecr.us-west-2.amazonaws.com/${var.boardgamegeek_scraper}_dev:latest"
  cpu                    = "256"
  memory                 = "2048"
  region                 = var.REGION
}

# module "" {
#     source = "./modules/ecs_task_definition"
#     task_definition_family=
#     task_definition_name =
#     registry_name="${data.aws_caller_identity.current.account_id}.dkr.ecr.us-west-2.amazonaws.com/${}:latest"
#     environment="prod"
#     env_file="arn:aws:s3:::${var.s3_scraper_task_bucket}/${}.env"
#     task_role_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${}_FargateTaskRole"
#     execution_role_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${}_FargateExecutionRole"
#     cpu ="2048"
#     memory ="16384"
#     region = var.REGION
# }
