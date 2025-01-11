variable "task_definition_name" {
  type = string
}

variable "region" {
  type = string
}

variable "account_id" {
  type = string
}

output "arn" {
  value = aws_iam_policy.ecs_run_permissions.arn
}

resource "aws_iam_policy" "ecs_run_permissions" {
  name        = "ecs_run_permissions_${var.task_definition_name}"
  description = "Policy to allow running the BGG ECS tasks"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "VisualEditor0",
        Effect = "Allow",
        Action = "ecs:DescribeTasks",
        Resource = [
          "arn:aws:ecs:${var.region}:${var.account_id}:task/*/${var.task_definition_name}",
          "arn:aws:ecs:${var.region}:${var.account_id}:task-definition/${var.task_definition_name}:*",
          "arn:aws:ecs:${var.region}:${var.account_id}:task/*/dev_${var.task_definition_name}",
          "arn:aws:ecs:${var.region}:${var.account_id}:task-definition/dev_${var.task_definition_name}:*",
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
          "arn:aws:ecs:${var.region}:${var.account_id}:task-definition/${var.task_definition_name}:*",
          "arn:aws:ecs:${var.region}:${var.account_id}:task-definition/dev_${var.task_definition_name}:*",
        ]
      },
      {
        Sid    = "VisualEditor3",
        Effect = "Allow",
        Action = "iam:PassRole",
        Resource = [
          "arn:aws:iam::${var.account_id}:role/${var.task_definition_name}_FargateExecutionRole",
          "arn:aws:iam::${var.account_id}:role/${var.task_definition_name}_FargateTaskRole"
        ]
      }
    ]
  })
}