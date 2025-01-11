resource "aws_s3_object" "file_upload" {
  bucket = var.S3_SCRAPER_BUCKET
  key    = "boardgamegeek.env"
  source = "../.env"
}

module "bgg_ratings_embedder_FargateExecutionRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "${var.bgg_ratings_embedder}_FargateExecutionRole"
}

module "bgg_ratings_embedder_FargateTaskRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "${var.bgg_ratings_embedder}_FargateTaskRole"
}

resource "aws_iam_role_policy_attachment" "S3_Access_bgg_ratings_embedder_FargateExecutionRole_attach" {
  role       = module.bgg_ratings_embedder_FargateExecutionRole_role.name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

resource "aws_iam_role_policy_attachment" "S3_Access_boardgamegeekbgg_ratings_embedder_FargateTaskRoleattach" {
  role       = module.bgg_ratings_embedder_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

resource "aws_iam_role_policy_attachment" "Cloudwatch_Put_Metricsbgg_ratings_embedder_FargateTaskRoleattach" {
  role       = module.bgg_ratings_embedder_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.Cloudwatch_Put_Metrics_policy.arn
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

module "bgg_ratings_data_cleaner_FargateTaskRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "${var.bgg_ratings_data_cleaner}_FargateTaskRole"
}

module "bgg_ratings_data_cleaner_FargateExecutionRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "${var.bgg_ratings_data_cleaner}_FargateExecutionRole"
}

resource "aws_iam_role_policy_attachment" "S3_Access_bgg_ratings_data_cleaner_FargateExecutionRole_attach" {
  role       = module.bgg_ratings_data_cleaner_FargateExecutionRole_role.name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

resource "aws_iam_role_policy_attachment" "S3_Access_boardgamegeekbgg_ratings_data_cleaner_FargateTaskRoleattach" {
  role       = module.bgg_ratings_data_cleaner_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

resource "aws_iam_role_policy_attachment" "Cloudwatch_Put_Metricsbgg_ratings_data_cleaner_FargateTaskRoleattach" {
  role       = module.bgg_ratings_data_cleaner_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.Cloudwatch_Put_Metrics_policy.arn
}

resource "aws_iam_role_policy_attachment" "glue_boardgamegeekbgg_ratings_data_cleaner_FargateTaskRoleattach" {
  role       = module.bgg_ratings_data_cleaner_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.glue_table_access.arn
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
module "rag_description_generation_FargateExecutionRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "${var.rag_description_generation}_FargateExecutionRole"
}

module "rag_description_generation_FargateTaskRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "${var.rag_description_generation}_FargateTaskRole"
}

resource "aws_iam_role_policy_attachment" "S3_Access_rag_description_generation_FargateExecutionRole_attach" {
  role       = module.rag_description_generation_FargateExecutionRole_role.name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

resource "aws_iam_role_policy_attachment" "S3_Access_rag_description_generation_FargateTaskRole_attach" {
  role       = module.rag_description_generation_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

resource "aws_iam_role_policy_attachment" "Cloudwatch_Put_Metrics_rag_description_generation_FargateTaskRole_roleattach" {
  role       = module.rag_description_generation_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.Cloudwatch_Put_Metrics_policy.arn
}

resource "aws_iam_role_policy_attachment" "dynamodb_rag_description_generation_FargateTaskRole_roleattach" {
  role       = module.rag_description_generation_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.game_generated_descriptions_dynamodb_access.arn
}

# not currently using EC2 for Weaviate server, but we'll keep this here for future use
# resource "aws_iam_role_policy_attachment" "rag_description_generation_SSM_send_command_attach" {
#   role       = module.rag_description_generation_FargateTaskRole_role.name
#   policy_arn = aws_iam_policy.SSM_send_command.arn
# }
# resource "aws_iam_role_policy_attachment" "ec2_instance_access_rag_description_generation_FargateTaskRole_roleattach" {
#   role       = module.rag_description_generation_FargateTaskRole_role.name
#   policy_arn = aws_iam_policy.ec2_instance_access.arn
# }

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

