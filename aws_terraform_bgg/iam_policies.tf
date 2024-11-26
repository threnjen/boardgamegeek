resource "aws_iam_policy" "S3_Access_bgg_scraper_policy" {
  name = "S3_Access_bgg_scraper"
  path = "/"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:ListBucket",
          "s3:PutObject",
          "s3:GetObject",
          "s3:GetObjectAttributes",
          "s3:DeleteObject"
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

module "bgg_scraper_describe_task_def_policy" {
  source = "./modules/lambda_ecs_trigger_policies"
  name   = "${var.bgg_scraper}_lambda_ecs_trigger"
  task_name = var.bgg_scraper
  region = var.REGION
  account_id = data.aws_caller_identity.current.account_id
}
module "bgg_game_data_cleaner_describe_task_def_policy" {
  source = "./modules/lambda_ecs_trigger_policies"
  name   = "${var.bgg_game_data_cleaner}_lambda_ecs_trigger"
  task_name = var.bgg_game_data_cleaner
  region = var.REGION
  account_id = data.aws_caller_identity.current.account_id
}

module "bgg_ratings_data_cleaner_describe_task_def_policy" {
  source = "./modules/lambda_ecs_trigger_policies"
  name   = "${var.bgg_ratings_data_cleaner}_lambda_ecs_trigger"
  task_name = var.bgg_ratings_data_cleaner
  region = var.REGION
  account_id = data.aws_caller_identity.current.account_id
}

module "bgg_users_data_cleaner_describe_task_def_policy" {
  source = "./modules/lambda_ecs_trigger_policies"
  name   = "${var.bgg_users_data_cleaner}_lambda_ecs_trigger"
  task_name = var.bgg_users_data_cleaner
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

module "trigger_bgg_generate_ratings_urls_lambda" {
  source = "./modules/iam_lambda_run_permissions"
  function_name = module.bgg_generate_ratings_urls.function_name
  region = var.REGION
  account_id = data.aws_caller_identity.current.account_id
}
resource "aws_iam_policy" "ecs_run_permissions_bgg_game_data_cleaner" {
  name        = "ecs_run_permissions_bgg_game_data_cleaner"
  description = "Policy to allow running the BGG ECS tasks"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "VisualEditor0",
        Effect = "Allow",
        Action = "ecs:DescribeTasks",
        Resource = [
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task/*/${var.bgg_game_data_cleaner}",
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task-definition/${var.bgg_game_data_cleaner}:*",
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task/*/dev_${var.bgg_game_data_cleaner}",
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task-definition/dev_${var.bgg_game_data_cleaner}:*",
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
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task-definition/${var.bgg_game_data_cleaner}:*",
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task-definition/dev_${var.bgg_game_data_cleaner}:*",
        ]
      },
      {
        Sid    = "VisualEditor3",
        Effect = "Allow",
        Action = "iam:PassRole",
        Resource = [
          "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_game_data_cleaner}_FargateExecutionRole",
          "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_game_data_cleaner}_FargateTaskRole"
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
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task/*/${var.bgg_scraper}",
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task-definition/${var.bgg_scraper}:*",
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task/*/dev_${var.bgg_scraper}",
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task-definition/dev_${var.bgg_scraper}:*"
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
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task-definition/${var.bgg_scraper}:*",
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task-definition/dev_${var.bgg_scraper}:*"
        ]
      },
      {
        Sid    = "VisualEditor3",
        Effect = "Allow",
        Action = "iam:PassRole",
        Resource = [
          "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_scraper}_FargateExecutionRole",
          "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_scraper}_FargateTaskRole"
        ]
      }
    ]
  })
}

resource "aws_iam_policy" "ecs_run_permissions_bgg_ratings_data_cleaner" {
  name        = "ecs_run_permissions_bgg_ratings_data_cleaner"
  description = "Policy to allow running the BGG ECS tasks"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "VisualEditor0",
        Effect = "Allow",
        Action = "ecs:DescribeTasks",
        Resource = [
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task/*/${var.bgg_ratings_data_cleaner}",
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task-definition/${var.bgg_ratings_data_cleaner}:*",
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task/*/dev_${var.bgg_ratings_data_cleaner}",
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task-definition/dev_${var.bgg_ratings_data_cleaner}:*",
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
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task-definition/${var.bgg_ratings_data_cleaner}:*",
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task-definition/dev_${var.bgg_ratings_data_cleaner}:*",
        ]
      },
      {
        Sid    = "VisualEditor3",
        Effect = "Allow",
        Action = "iam:PassRole",
        Resource = [
          "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_ratings_data_cleaner}_FargateExecutionRole",
          "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_ratings_data_cleaner}_FargateTaskRole"
        ]
      }
    ]
  })
}

resource "aws_iam_policy" "ecs_run_permissions_bgg_users_data_cleaner" {
  name        = "ecs_run_permissions_bgg_users_data_cleaner"
  description = "Policy to allow running the BGG ECS tasks"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "VisualEditor0",
        Effect = "Allow",
        Action = "ecs:DescribeTasks",
        Resource = [
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task/*/${var.bgg_users_data_cleaner}",
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task-definition/${var.bgg_users_data_cleaner}:*",
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task/*/dev_${var.bgg_users_data_cleaner}",
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task-definition/dev_${var.bgg_users_data_cleaner}:*",
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
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task-definition/${var.bgg_users_data_cleaner}:*",
          "arn:aws:ecs:${var.REGION}:${data.aws_caller_identity.current.account_id}:task-definition/dev_${var.bgg_users_data_cleaner}:*",
        ]
      },
      {
        Sid    = "VisualEditor3",
        Effect = "Allow",
        Action = "iam:PassRole",
        Resource = [
          "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_users_data_cleaner}_FargateExecutionRole",
          "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_users_data_cleaner}_FargateTaskRole"
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
        Resource = concat([for function in local.lambda_functions : "arn:aws:lambda:${var.REGION}:${data.aws_caller_identity.current.account_id}:function:${function}"], ["${aws_lambda_function.bgg_boardgame_file_retrieval_lambda.arn}"])
      },
    ]
  })
}


resource "aws_iam_policy" "glue_table_access" {
  name        = "glue_access_permissions"
  description = "Policy to allow running access to Glue tables for BGG Scraper/Cleaner tasks"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid = "GlueTableAccess"
        Action = [
          "glue:CreateTable",
                "glue:GetTable",
                "glue:GetTables",                
                "glue:UpdateTable",
                "glue:DeleteTable",
                "glue:BatchDeleteTable",
                "glue:GetTableVersion",
                "glue:GetTableVersions",
                "glue:DeleteTableVersion",
                "glue:BatchDeleteTableVersion",
                "glue:CreatePartition",
                "glue:BatchCreatePartition",
                "glue:GetPartition",
                "glue:GetPartitions",
                "glue:BatchGetPartition",
                "glue:UpdatePartition",
                "glue:DeletePartition",
                "glue:BatchDeletePartition"
        ]
        Effect   = "Allow"
        Resource = [
        "arn:aws:glue:${var.REGION}:${data.aws_caller_identity.current.account_id}:catalog",
        "arn:aws:glue:${var.REGION}:${data.aws_caller_identity.current.account_id}:database/boardgamegeek",
        "arn:aws:glue:${var.REGION}:${data.aws_caller_identity.current.account_id}:table/boardgamegeek/*"

        ]
      },
    ]
  })
}