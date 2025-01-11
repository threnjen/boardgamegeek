
module "ecs_run_permissions_bgg_game_data_cleaner" {
  source               = "./modules/fargate_iam_policies"
  task_definition_name = var.bgg_game_data_cleaner
  region               = var.REGION
  account_id           = data.aws_caller_identity.current.account_id
}

module "ecs_run_permissions_bgg_scraper" {
  source               = "./modules/fargate_iam_policies"
  task_definition_name = var.bgg_scraper
  region               = var.REGION
  account_id           = data.aws_caller_identity.current.account_id
}

module "ecs_run_permissions_bgg_ratings_data_cleaner" {
  source               = "./modules/fargate_iam_policies"
  task_definition_name = var.bgg_ratings_data_cleaner
  region               = var.REGION
  account_id           = data.aws_caller_identity.current.account_id
}

module "ecs_run_permissions_bgg_users_data_cleaner" {
  source               = "./modules/fargate_iam_policies"
  task_definition_name = var.bgg_users_data_cleaner
  region               = var.REGION
  account_id           = data.aws_caller_identity.current.account_id
}

module "ecs_run_permissions_bgg_ratings_embedder" {
  source               = "./modules/fargate_iam_policies"
  task_definition_name = var.bgg_ratings_embedder
  region               = var.REGION
  account_id           = data.aws_caller_identity.current.account_id
}




