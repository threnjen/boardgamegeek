
variable "bgg_generate_urls" {
  description = "The name of the ECS task definition for the bgg_scraper"
  type        = string
  default     = "bgg_generate_urls"
}

module "bgg_generate_urls" {
  source        = "./modules/lambda_function_direct"
  function_name = "${var.bgg_generate_urls}_${var.RESOURCE_ENV}"
  timeout       = 900
  memory_size   = 1024
  role          = module.bgg_generate_urls_lambda_role.arn
  handler       = "bgg_generate_urls.lambda_handler"
  layers        = ["arn:aws:lambda:${var.REGION}:336392948345:layer:AWSSDKPandas-Python312:13"]
  description   = "Lambda function to generate game urls"
  RESOURCE_ENV = var.RESOURCE_ENV
}

module "bgg_generate_urls_lambda_role" {
  source    = "./modules/iam_lambda_roles"
  role_name = "bgg_generate_urls_lambda_role"
}
resource "aws_iam_role_policy_attachment" "bgg_generate_urls_lambda_role" {
  role       = module.bgg_generate_urls_lambda_role.role_name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
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