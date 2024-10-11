resource "aws_lambda_function" "lambda" {
  filename         = "lambda_function.zip"
  function_name    = var.function_name
  timeout          = var.timeout
  memory_size      = var.memory_size
  role             = var.role
  handler          = var.handler
  runtime = "python3.12"

  layers = var.layers

  source_code_hash = filebase64sha256("lambda_function.zip")
  
  environment {
    variables = merge(
      { for tuple in regexall("(.*?)=(.*)", file(".env")) : tuple[0] => tuple[1] },
      {
        ENV = var.environment
        IS_LOCAL=false
      }
    )
  }
}

output "function_name" {
  value = aws_lambda_function.lambda.function_name
}