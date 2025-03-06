resource "aws_dynamodb_table" "game_stats-dynamodb-table" {
  name                        = "game_stats"
  hash_key                    = "game_id"
  billing_mode                = "PAY_PER_REQUEST"
  deletion_protection_enabled = true

  attribute {
    name = "game_id"
    type = "S"
  }

  tags = {
    Name        = "game_stats"
    Environment = "prod"
  }
}

resource "aws_dynamodb_table" "dev_game_stats-dynamodb-table" {
  name                        = "dev_game_stats"
  hash_key                    = "game_id"

  billing_mode                = "PAY_PER_REQUEST"
  deletion_protection_enabled = true

  attribute {
    name = "game_id"
    type = "S"
  }


  tags = {
    Name        = "dev_game_stats"
    Environment = "dev"
  }
}

resource "aws_dynamodb_table" "game_ratings-dynamodb-table" {
  name                        = "game_ratings"
  hash_key                    = "game_id"
  range_key                   = "username"
  billing_mode                = "PAY_PER_REQUEST"
  deletion_protection_enabled = true

  attribute {
    name = "game_id"
    type = "S"
  }
  attribute {
    name = "username"
    type = "S"
  }
  tags = {
    Name        = "game_ratings"
    Environment = "prod"
  }
}

resource "aws_dynamodb_table" "dev_game_ratings-dynamodb-table" {
  name                        = "dev_game_ratings"
  hash_key                    = "game_id"
  range_key                   = "username"
  billing_mode                = "PAY_PER_REQUEST"
  deletion_protection_enabled = true

  attribute {
    name = "game_id"
    type = "S"
  }
      attribute {
    name = "username"
    type = "S"
  }

  tags = {
    Name        = "dev_game_ratings"
    Environment = "dev"
  }
}

resource "aws_iam_policy" "game_stats_dynamodb_access" {
  name = "game_stats_dynamodb_access"
  path = "/"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "ListAllTables",
        Effect = "Allow",
        Action = [
          "dynamodb:ListTables",
        ],
        Resource = "*"
      },
      {
        Sid    = "PutGetItems",
        Effect = "Allow",
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:BatchWriteItem"
        ],
        Resource = [
          aws_dynamodb_table.game_stats-dynamodb-table.arn,
          aws_dynamodb_table.dev_game_stats-dynamodb-table.arn,
        ]
      }
    ]
  })
}

resource "aws_iam_policy" "game_ratings_dynamodb_access" {
  name = "game_ratings_dynamodb_access"
  path = "/"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "ListAllTables",
        Effect = "Allow",
        Action = [
          "dynamodb:ListTables",
        ],
        Resource = "*"
      },
      {
        Sid    = "PutGetItems",
        Effect = "Allow",
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:BatchWriteItem"
        ],
        Resource = [
          aws_dynamodb_table.game_ratings-dynamodb-table.arn,
          aws_dynamodb_table.dev_game_ratings-dynamodb-table.arn
        ]
      }
    ]
  })
}

variable "bgg_dynamodb_data_store" {
  description = "The name of the ECS task definition for the bgg_dynamodb_data_store"
  type        = string
  default     = "bgg_dynamodb_data_store"
}

module "bgg_dynamodb_data_store_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = var.bgg_dynamodb_data_store
}

module "dev_bgg_dynamodb_data_store_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = "dev_${var.bgg_dynamodb_data_store}"
}

module "ecs_run_permissions_bgg_dynamodb_data_store" {
  source               = "./modules/fargate_iam_policies"
  task_definition_name = var.bgg_dynamodb_data_store
  region               = var.REGION
  account_id           = data.aws_caller_identity.current.account_id
}

module "bgg_dynamodb_data_store_ecs" {
  source                 = "./modules/ecs_task_definition"
  task_definition_family = var.bgg_dynamodb_data_store
  task_definition_name   = var.bgg_dynamodb_data_store
  registry_name          = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.bgg_dynamodb_data_store}:latest"
  environment            = "prod"
  env_file               = "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/boardgamegeek.env"
  task_role_arn          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_dynamodb_data_store}_FargateTaskRole"
  execution_role_arn     = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_dynamodb_data_store}_FargateExecutionRole"
  image                  = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.bgg_dynamodb_data_store}:latest"
  cpu                    = "2048"
  memory                 = "16384"
  region                 = var.REGION
}

module "dev_bgg_dynamodb_data_store_ecs" {
  source                 = "./modules/ecs_task_definition"
  task_definition_family = "dev_${var.bgg_dynamodb_data_store}"
  task_definition_name   = "dev_${var.bgg_dynamodb_data_store}"
  registry_name          = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/dev_${var.bgg_dynamodb_data_store}:latest"
  environment            = "dev"
  env_file               = "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/boardgamegeek.env"
  task_role_arn          = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_dynamodb_data_store}_FargateTaskRole"
  execution_role_arn     = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.bgg_dynamodb_data_store}_FargateExecutionRole"
  image                  = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/dev_${var.bgg_dynamodb_data_store}:latest"
  cpu                    = "256"
  memory                 = "1024"
  region                 = var.REGION
}

module "bgg_dynamodb_data_store_FargateExecutionRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "${var.bgg_dynamodb_data_store}_FargateExecutionRole"
}

module "bgg_dynamodb_data_store_FargateTaskRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "${var.bgg_dynamodb_data_store}_FargateTaskRole"
}

resource "aws_iam_role_policy_attachment" "S3_Access_bgg_dynamodb_data_store_FargateExecutionRole_attach" {
  role       = module.bgg_dynamodb_data_store_FargateExecutionRole_role.name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

resource "aws_iam_role_policy_attachment" "S3_Access_boardgamegeekbgg_dynamodb_data_store_FargateTaskRoleattach" {
  role       = module.bgg_dynamodb_data_store_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

resource "aws_iam_role_policy_attachment" "Cloudwatch_Put_Metricsbgg_dynamodb_data_store_FargateTaskRoleattach" {
  role       = module.bgg_dynamodb_data_store_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.Cloudwatch_Put_Metrics_policy.arn
}

resource "aws_iam_role_policy_attachment" "game_stats_dynamodb_access_FargateTaskRoleattach" {
  role       = module.bgg_dynamodb_data_store_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.game_stats_dynamodb_access.arn
}

resource "aws_iam_role_policy_attachment" "bgg_game_ratings_dynamodb_access_FargateTaskRoleattach" {
  role       = module.bgg_dynamodb_data_store_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.game_ratings_dynamodb_access.arn
}



# module "bgg_dynamodb_data_store_fargate_trigger" {
#   source        = "./modules/lambda_function_direct"
#   function_name = "${var.bgg_dynamodb_data_store}_fargate_trigger"
#   timeout       = 600
#   memory_size   = 128
#   role          = module.bgg_dynamodb_data_store_fargate_trigger_role.arn
#   handler       = "${var.bgg_dynamodb_data_store}_fargate_trigger.lambda_handler"
#   layers        = ["arn:aws:lambda:${var.REGION}:336392948345:layer:AWSSDKPandas-Python312:13"]
#   environment   = "prod"
#   description   = "Lambda function to trigger the boardgamegeek cleaner fargate task"
# }


# module "dev_bgg_dynamodb_data_store_fargate_trigger" {
#   source        = "./modules/lambda_function_direct"
#   function_name = "dev_bgg_dynamodb_data_store_fargate_trigger"
#   timeout       = 600
#   memory_size   = 128
#   role          = module.bgg_dynamodb_data_store_fargate_trigger_role.arn
#   handler       = "${var.bgg_dynamodb_data_store}_fargate_trigger.lambda_handler"
#   layers        = ["arn:aws:lambda:${var.REGION}:336392948345:layer:AWSSDKPandas-Python312:13"]
#   environment   = "dev"
#   description   = "DEV Lambda function to trigger the boardgamegeek cleaner fargate task"
# }


# module "bgg_dynamodb_data_store_fargate_trigger_role" {
#   source    = "./modules/iam_lambda_roles"
#   role_name = "${var.bgg_dynamodb_data_store}_fargate_trigger_role"
# }

# resource "aws_iam_role_policy_attachment" "bgg_dynamodb_data_store_describe_attach" {
#   role       = module.bgg_dynamodb_data_store_fargate_trigger_role.role_name
#   policy_arn = module.bgg_dynamodb_data_store_describe_task_def_policy.lambda_ecs_trigger_arn
# }

# resource "aws_iam_role_policy_attachment" "bgg_dynamodb_data_store_s3_attach" {
#   role       = module.bgg_dynamodb_data_store_fargate_trigger_role.role_name
#   policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
# }

# module "bgg_dynamodb_data_store_describe_task_def_policy" {
#   source     = "./modules/lambda_ecs_trigger_policies"
#   name       = "${var.bgg_dynamodb_data_store}_lambda_ecs_trigger"
#   task_name  = var.bgg_dynamodb_data_store
#   region     = var.REGION
#   account_id = data.aws_caller_identity.current.account_id
# }