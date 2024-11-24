resource "aws_ecs_cluster" "boardgamegeek" {
  name = "boardgamegeek"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

module "boardgamegeek_orchestrator_ecs" {
  source                 = "./modules/ecs_task_definition"
  task_definition_family = var.boardgamegeek_orchestrator
  task_definition_name   = var.boardgamegeek_orchestrator
  registry_name          = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.boardgamegeek_orchestrator}:latest"
  environment            = "prod"
  env_file               = "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/boardgamegeek.env"
  task_role_arn          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.boardgamegeek_orchestrator}_FargateTaskRole"
  execution_role_arn     = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.boardgamegeek_orchestrator}_FargateExecutionRole"
  image                  = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.boardgamegeek_orchestrator}:latest"
  cpu                    = "1024"
  memory                 = "4096"
  region                 = var.REGION
}

module "dev_boardgamegeek_orchestrator_ecs" {
  source                 = "./modules/ecs_task_definition"
  task_definition_family = "dev_${var.boardgamegeek_orchestrator}"
  task_definition_name   = "dev_${var.boardgamegeek_orchestrator}"
  registry_name          = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.boardgamegeek_orchestrator}:latest"
  environment            = "dev"
  env_file               = "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/boardgamegeek.env"
  task_role_arn          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.boardgamegeek_orchestrator}_FargateTaskRole"
  execution_role_arn     = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.boardgamegeek_orchestrator}_FargateExecutionRole"
  image                  = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/dev_${var.boardgamegeek_orchestrator}:latest"
  cpu                    = "1024"
  memory                 = "4096"
  region                 = var.REGION
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
  cpu                    = "2048"
  memory                 = "8192"
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

module "bgg_user_data_cleaner_ecs" {
  source                 = "./modules/ecs_task_definition"
  task_definition_family = var.bgg_user_data_cleaner
  task_definition_name   = var.bgg_user_data_cleaner
  registry_name          = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.bgg_user_data_cleaner}:latest"
  environment            = "prod"
  env_file               = "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/boardgamegeek.env"
  task_role_arn          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_user_data_cleaner}_FargateTaskRole"
  execution_role_arn     = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_user_data_cleaner}_FargateExecutionRole"
  image                  = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.bgg_user_data_cleaner}:latest"
  cpu                    = "4096"
  memory                 = "24576"
  region                 = var.REGION
}

module "dev_bgg_user_data_cleaner_ecs" {
  source                 = "./modules/ecs_task_definition"
  task_definition_family = "dev_${var.bgg_user_data_cleaner}"
  task_definition_name   = "dev_${var.bgg_user_data_cleaner}"
  registry_name          = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/dev_${var.bgg_user_data_cleaner}:latest"
  environment            = "dev"
  env_file               = "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/boardgamegeek.env"
  task_role_arn          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_user_data_cleaner}_FargateTaskRole"
  execution_role_arn     = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_user_data_cleaner}_FargateExecutionRole"
  image                  = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/dev_${var.bgg_user_data_cleaner}:latest"
  cpu                    = "512"
  memory                 = "4096"
  region                 = var.REGION
}


