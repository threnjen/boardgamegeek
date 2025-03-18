output "lambda_arn" {
  value = aws_iam_policy.lambda_trigger_permissions.arn
}

resource "aws_iam_policy" "lambda_trigger_permissions" {
  name        = "${var.function_name}_lambda_trigger_permissions"
  description = "Policy to allow triggering of the Lambda function ${var.function_name}"

  # Terraform's "jsonencode" function converts a
  # Terraform expression result to valid JSON syntax.
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid = "TriggerLambdaFunction"
        Action = [
          "lambda:InvokeFunction*",
        ]
        Effect   = "Allow"
        Resource = "arn:aws:lambda:${var.region}:${var.account_id}:function:${var.function_name}"
      },
    ]
  })
}