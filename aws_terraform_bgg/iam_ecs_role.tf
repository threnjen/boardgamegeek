resource "aws_s3_object" "file_upload" {
  bucket = var.S3_SCRAPER_BUCKET
  key    = "boardgamegeek.env"
  source = "../.env"
}

module "bgg_orchestrator_FargateExecutionRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "bgg_orchestrator_FargateExecutionRole"
}

resource "aws_iam_role_policy_attachment" "S3_Access_bgg_orchestrator_FargateExecutionRole_attach" {
  role       = module.bgg_orchestrator_FargateExecutionRole_role.name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

module "bgg_orchestrator_FargateTaskRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "bgg_orchestrator_FargateTaskRole"
}

resource "aws_iam_role_policy_attachment" "S3_Access_bgg_orchestrator_FargateTaskRole_attach" {
  role       = module.bgg_orchestrator_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

resource "aws_iam_role_policy_attachment" "Cloudwatch_Put_Metrics_bgg_orchestrator_FargateTaskRole_roleattach" {
  role       = module.bgg_orchestrator_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.Cloudwatch_Put_Metrics_policy.arn
}

module "bgg_game_data_cleaner_FargateExecutionRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "bgg_game_data_cleaner_FargateExecutionRole"
}

resource "aws_iam_role_policy_attachment" "S3_Access_bgg_game_data_cleaner_FargateExecutionRole_attach" {
  role       = module.bgg_game_data_cleaner_FargateExecutionRole_role.name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

module "bgg_game_data_cleaner_FargateTaskRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "bgg_game_data_cleaner_FargateTaskRole"
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

module "bgg_scraper_FargateExecutionRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "bgg_scraper_FargateExecutionRole"
}
resource "aws_iam_role_policy_attachment" "S3_Access_bgg_scraperbgg_scraper_FargateExecutionRole" {
  role       = module.bgg_scraper_FargateExecutionRole_role.name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

module "bgg_scraper_FargateTaskRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "bgg_scraper_FargateTaskRole"
}
resource "aws_iam_role_policy_attachment" "S3_Access_boardgamegeekbgg_scraper_FargateTaskRoleattach" {
  role       = module.bgg_scraper_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

resource "aws_iam_role_policy_attachment" "Cloudwatch_Put_Metric_bgg_scraper_FargateTaskRoleattach" {
  role       = module.bgg_scraper_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.Cloudwatch_Put_Metrics_policy.arn
}

resource "aws_iam_role_policy_attachment" "trigger_bgg_lambda_run_attach_to_orchestrator" {
  role       = module.bgg_orchestrator_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.lambda_direct_permissions.arn
}

resource "aws_iam_role_policy_attachment" "ecs_run_attach_cleaner_to_orchestrator" {
  role       = module.bgg_orchestrator_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.ecs_run_permissions_bgg_game_data_cleaner.arn
}

resource "aws_iam_role_policy_attachment" "ecs_run_attach_scraper_to_orchestrator" {
  role       = module.bgg_orchestrator_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.ecs_run_permissions_bgg_scraper.arn
}

