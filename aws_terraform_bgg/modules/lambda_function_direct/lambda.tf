resource "aws_lambda_function" "lambda" {
  filename         = "lambda_function.zip"
  function_name    = var.function_name
  timeout          = var.timeout
  memory_size      = var.memory_size
  role             = var.role
  handler          = var.handler
  runtime = "python3.12"
  description = var.description
  layers = var.layers

  source_code_hash = filebase64sha256("lambda_function.zip")
  
  environment {
    variables = merge(
      { 
      for tuple in regexall("(.*?)=(.*)", file("../.env")) : tuple[0] => tuple[1] 
      if !(tuple[0] == "IS_LOCAL" || tuple[0] == "ENVIRONMENT" || tuple[0] == "PYTHONPATH")
    },
      {
        ENVIRONMENT = var.environment
        IS_LOCAL=false
      }
    )
  }
}

output "function_name" {
  value = aws_lambda_function.lambda.function_name
}

resource "aws_cloudwatch_log_group" "cloudwatch_log_group" {
  name = "/aws/lambda/${var.function_name}"

  retention_in_days = 3
}