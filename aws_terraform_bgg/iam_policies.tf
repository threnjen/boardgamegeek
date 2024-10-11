resource "aws_iam_policy" "S3_Access_boardgamegeek_scraper_policy" {
  name = "S3_Access_boardgamegeek_scraper"
  path = "/"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:ListBucket",
          "s3:PutObject",
          "s3:GetObject"
        ]
        Effect   = "Allow"
        Resource = "arn:aws:s3:::boardgamegeek_scraper"
      },
      { Action = [
        "s3:ListAllMyBuckets"
        ]
        Effect = "Allow"
      Resource = "*" }
    ]
  })
}

resource "aws_iam_policy" "Cloudwatch_Put_Metrics_policy" {
  name = "Cloudwatch_Put_Metrics"
  path = "/"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "VisualEditor0",
        Effect = "Allow",
        Action = [
          "cloudwatch:PutMetricAlarm",
          "cloudwatch:PutMetricData"
        ],
        Resource = "*"
      }
    ]
  })
}

module "bgg_cleaner_fargate_trigger_cloudwatch_policy" {
  source = "./modules/lambda_ecs_trigger_policies"
  name   = "${var.boardgamegeek_cleaner}_fargate_trigger_cloudwatch"
  task_name = var.boardgamegeek_cleaner
  region = var.REGION
  account_id = data.aws_caller_identity.current.account_id
}

module "bgg_scraper_fargate_trigger_cloudwatch_policy" {
  source = "./modules/lambda_ecs_trigger_policies"
  name   = "${var.boardgamegeek_scraper}_fargate_trigger_cloudwatch"
  task_name = var.boardgamegeek_scraper
  region = var.REGION
  account_id = data.aws_caller_identity.current.account_id
}
module "bgg_scraper_describe_task_def_policy" {
  source = "./modules/lambda_ecs_trigger_policies"
  name   = "${var.boardgamegeek_scraper}_lambda_ecs_trigger"
  task_name = var.boardgamegeek_scraper
  region = var.REGION
  account_id = data.aws_caller_identity.current.account_id
}
module "bgg_cleaner_describe_task_def_policy" {
  source = "./modules/lambda_ecs_trigger_policies"
  name   = "${var.boardgamegeek_cleaner}_lambda_ecs_trigger"
  task_name = var.boardgamegeek_cleaner
  region = var.REGION
  account_id = data.aws_caller_identity.current.account_id
}
