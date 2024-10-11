module "boardgamegeek_cleaner_FargateExecutionRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "boardgamegeek_cleaner_FargateExecutionRole"
}

resource "aws_iam_role_policy_attachment" "S3_Access_boardgamegeek_cleaner_FargateExecutionRole_attach" {
  role       = module.boardgamegeek_cleaner_FargateExecutionRole_role.name
  policy_arn = aws_iam_policy.S3_Access_boardgamegeek_scraper_policy.arn
}

module "boardgamegeek_cleaner_FargateTaskRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "boardgamegeek_cleaner_FargateTaskRole"
}

resource "aws_iam_role_policy_attachment" "S3_Access_boardgamegeekboardgamegeek_cleaner_FargateTaskRoleattach" {
  role       = module.boardgamegeek_cleaner_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.S3_Access_boardgamegeek_scraper_policy.arn
}

resource "aws_iam_role_policy_attachment" "Cloudwatch_Put_Metricsboardgamegeek_cleaner_FargateTaskRoleattach" {
  role       = module.boardgamegeek_cleaner_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.Cloudwatch_Put_Metrics_policy.arn
}

module "boardgamegeek_scraper_FargateExecutionRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "boardgamegeek_scraper_FargateExecutionRole"
}
resource "aws_iam_role_policy_attachment" "S3_Access_boardgamegeek_scraperboardgamegeek_scraper_FargateExecutionRole" {
  role       = module.boardgamegeek_scraper_FargateExecutionRole_role.name
  policy_arn = aws_iam_policy.S3_Access_boardgamegeek_scraper_policy.arn
}

module "boardgamegeek_scraper_FargateTaskRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "boardgamegeek_scraper_FargateTaskRole"
}
resource "aws_iam_role_policy_attachment" "S3_Access_boardgamegeekboardgamegeek_scraper_FargateTaskRoleattach" {
  role       = module.boardgamegeek_scraper_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.S3_Access_boardgamegeek_scraper_policy.arn
}

resource "aws_iam_role_policy_attachment" "Cloudwatch_Put_Metricsboardgamegeek_scraper_FargateTaskRoleattach" {
  role       = module.boardgamegeek_scraper_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.Cloudwatch_Put_Metrics_policy.arn
}
