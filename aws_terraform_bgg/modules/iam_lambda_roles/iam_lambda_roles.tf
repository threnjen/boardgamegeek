data "aws_iam_policy_document" "assume_role_lambda" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

output "name" {
  value = aws_iam_role.lambda_role.name
}

output "arn" {
  value = aws_iam_role.lambda_role.arn
}

output "role_name" {
  value = aws_iam_role.lambda_role.name
}

resource "aws_iam_role" "lambda_role" {
  name               = var.role_name
  assume_role_policy = data.aws_iam_policy_document.assume_role_lambda.json
}

resource "aws_iam_role_policy_attachment" "lambda_role_basic_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = var.AWSLambdaBasicExecutionRole
}