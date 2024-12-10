

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
        Action   = ["ecs:DescribeTaskDefinition", "ecs:ListTasks"]
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
        Action   = ["ecs:DescribeTaskDefinition", "ecs:ListTasks"]
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
        Action   = ["ecs:DescribeTaskDefinition", "ecs:ListTasks"]
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
        Action   = ["ecs:DescribeTaskDefinition", "ecs:ListTasks"]
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



