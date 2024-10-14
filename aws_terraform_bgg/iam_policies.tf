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
          "s3:GetObject",
          "s3:GetObjectAttributes"
        ]
        Effect   = "Allow"
        Resource = [
				"arn:aws:s3:::${var.S3_SCRAPER_BUCKET}",
				"arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/*",
        "arn:aws:s3:::${var.BUCKET}",
				"arn:aws:s3:::${var.BUCKET}/*"
			]
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

# module "bgg_cleaner_fargate_trigger_cloudwatch_policy" {
#   source = "./modules/lambda_ecs_trigger_policies"
#   name   = "${var.boardgamegeek_cleaner}_cloudwatch"
#   task_name = var.boardgamegeek_cleaner
#   region = var.REGION
#   account_id = data.aws_caller_identity.current.account_id
# }

# module "bgg_scraper_fargate_trigger_cloudwatch_policy" {
#   source = "./modules/lambda_ecs_trigger_policies"
#   name   = "${var.boardgamegeek_scraper}_cloudwatch"
#   task_name = var.boardgamegeek_scraper
#   region = var.REGION
#   account_id = data.aws_caller_identity.current.account_id
# }
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

module "bgg_orchestrator_task_def_policy" {
  source = "./modules/lambda_ecs_trigger_policies"
  name   = "${var.boardgamegeek_orchestrator}_lambda_ecs_trigger"
  task_name = var.boardgamegeek_orchestrator
  region = var.REGION
  account_id = data.aws_caller_identity.current.account_id
}
module "trigger_bgg_generate_game_urls_lambda" {
  source = "./modules/iam_lambda_run_permissions"
  function_name = module.bgg_generate_game_urls.function_name
  region = var.REGION
  account_id = data.aws_caller_identity.current.account_id
}

module "trigger_bgg_generate_user_urls_lambda" {
  source = "./modules/iam_lambda_run_permissions"
  function_name = module.bgg_generate_user_urls.function_name
  region = var.REGION
  account_id = data.aws_caller_identity.current.account_id
}


# resource "aws_iam_policy" "lambda_trigger_permissions" {
#   name        = "lambda_trigger_run_permissions"
#   description = "Policy to allow triggering of the Lambda trigger functions"

#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Sid = "TriggerLambdaFunction"
#         Action = [
#           "lambda:InvokeFunction*",
#         ]
#         Effect   = "Allow"
#         Resource = [
#         "arn:aws:lambda:${var.REGION}:${data.aws_caller_identity.current.account_id}:function:${module.boardgame_scraper_fargate_trigger.function_name}",
#         "arn:aws:lambda:${var.REGION}:${data.aws_caller_identity.current.account_id}:function:${module.boardgame_scraper_fargate_trigger_dev.function_name}",
#         "arn:aws:lambda:${var.REGION}:${data.aws_caller_identity.current.account_id}:function:${module.boardgamegeek_cleaner_fargate_trigger.function_name}",
#         "arn:aws:lambda:${var.REGION}:${data.aws_caller_identity.current.account_id}:function:${module.boardgamegeek_cleaner_fargate_trigger_dev.function_name}"
#         ]
#       },
#     ]
#   })
# }

resource "aws_iam_policy" "ecs_run_permissions_bgg_cleaner" {
  name        = "ecs_run_permissions_bgg_cleaner"
  description = "Policy to allow running the BGG ECS tasks"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "VisualEditor0",
        Effect = "Allow",
        Action = "ecs:DescribeTasks",
        Resource = [
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task/*/${var.boardgamegeek_cleaner}",
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task-definition/${var.boardgamegeek_cleaner}:*",
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task/*/${var.boardgamegeek_cleaner}_dev",
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task-definition/${var.boardgamegeek_cleaner}_dev:*",
        ]
      },
      {
        Sid      = "VisualEditor1",
        Effect   = "Allow",
        Action   = "ecs:DescribeTaskDefinition",
        Resource = "*"
      },
      {
        Sid    = "VisualEditor2",
        Effect = "Allow",
        Action = "ecs:RunTask",
        Resource = [
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task-definition/${var.boardgamegeek_cleaner}:*",
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task-definition/${var.boardgamegeek_cleaner}_dev:*",
        ]
      },
      {
        Sid    = "VisualEditor3",
        Effect = "Allow",
        Action = "iam:PassRole",
        Resource = [
          "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.boardgamegeek_cleaner}_FargateExecutionRole",
          "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.boardgamegeek_cleaner}_FargateTaskRole"
        ]
      }
    ]
  })
}
resource "aws_iam_policy" "ecs_run_permissions_bgg_scraper" {
  name        = "ecs_run_permissions_bgg_scraper"
  description = "Policy to allow running the BGG ECS tasks"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "VisualEditor0",
        Effect = "Allow",
        Action = "ecs:DescribeTasks",
        Resource = [
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task/*/${var.boardgamegeek_scraper}",
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task-definition/${var.boardgamegeek_scraper}:*",
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task/*/${var.boardgamegeek_scraper}_dev",
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task-definition/${var.boardgamegeek_scraper}_dev:*"
        ]
      },
      {
        Sid      = "VisualEditor1",
        Effect   = "Allow",
        Action   = "ecs:DescribeTaskDefinition",
        Resource = "*"
      },
      {
        Sid    = "VisualEditor2",
        Effect = "Allow",
        Action = "ecs:RunTask",
        Resource = [
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task-definition/${var.boardgamegeek_scraper}:*",
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task-definition/${var.boardgamegeek_scraper}_dev:*"
        ]
      },
      {
        Sid    = "VisualEditor3",
        Effect = "Allow",
        Action = "iam:PassRole",
        Resource = [
          "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.boardgamegeek_scraper}_FargateExecutionRole",
          "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.boardgamegeek_scraper}_FargateTaskRole"
        ]
      }
    ]
  })
}



resource "aws_iam_policy" "lambda_direct_permissions" {
  name        = "lambda_run_permissions"
  description = "Policy to allow running of the Lambda functions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid = "TriggerLambdaFunction"
        Action = [
          "lambda:InvokeFunction*",
        ]
        Effect   = "Allow"
        Resource = [
        "arn:aws:lambda:${var.REGION}:${data.aws_caller_identity.current.account_id}:function:${module.bgg_generate_game_urls.function_name}",
        "arn:aws:lambda:${var.REGION}:${data.aws_caller_identity.current.account_id}:function:${module.bgg_generate_user_urls.function_name}",
        "${aws_lambda_function.bgg_boardgame_file_retrieval_lambda.arn}"
        ]
      },
    ]
  })
}
