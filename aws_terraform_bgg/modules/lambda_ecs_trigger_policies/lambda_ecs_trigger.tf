output "lambda_ecs_trigger_arn" {
  value = aws_iam_policy.lambda_ecs_trigger.arn
}


output "cloudwatch_arn" {
  value = aws_iam_policy.fargate_trigger_cloudwatch.arn
}

resource "aws_iam_policy" "lambda_ecs_trigger" {
  name = var.name
  path = "/"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "VisualEditor0",
        Effect = "Allow",
        Action = "ecs:DescribeTasks",
        Resource = [
          "arn:aws:ecs:${var.region}:${var.account_id}:task/*/${var.task_name}",
          "arn:aws:ecs:${var.region}:${var.account_id}:task-definition/${var.task_name}:*",
          "arn:aws:ecs:${var.region}:${var.account_id}:task/*/dev_${var.task_name}",
          "arn:aws:ecs:${var.region}:${var.account_id}:task-definition/dev_${var.task_name}:*"
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
          "arn:aws:ecs:${var.region}:${var.account_id}:task-definition/${var.task_name}:*",
          "arn:aws:ecs:${var.region}:${var.account_id}:task-definition/dev_${var.task_name}:*"
        ]
      },
      {
        Sid    = "VisualEditor3",
        Effect = "Allow",
        Action = "iam:PassRole",
        Resource = [
          "arn:aws:iam::${var.account_id}:role/${var.task_name}_FargateExecutionRole",
          "arn:aws:iam::${var.account_id}:role/${var.task_name}_FargateTaskRole"
        ]
      }
    ]
  })
}

resource "aws_iam_policy" "fargate_trigger_cloudwatch" {
  name = "${var.task_name}_fargate_trigger_cloudwatch"
  path = "/"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = "logs:CreateLogGroup",
        Resource = "arn:aws:logs:${var.region}:${var.account_id}:*"
      },
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = [
          "arn:aws:logs:${var.region}:${var.account_id}:log-group:/aws/lambda/${var.task_name}_fargate_trigger_dev:*",
          "arn:aws:logs:${var.region}:${var.account_id}:log-group:/aws/lambda/${var.task_name}_fargate_trigger:*"
        ]
      }
    ]
  })
}