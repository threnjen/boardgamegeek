


module "bgg_generate_game_urls" {
  source        = "./modules/lambda_function_direct"
  function_name = "bgg_generate_game_urls"
  timeout       = 900
  memory_size   = 1024
  role          = module.bgg_generate_game_urls_lambda_role.arn
  handler       = "generate_game_urls_lambda.lambda_handler"
  layers        = ["arn:aws:lambda:${var.REGION}:336392948345:layer:AWSSDKPandas-Python312:13"]
  environment   = "prod"
  description   = "Lambda function to generate game urls"
}

module "dev_bgg_generate_game_urls" {
  source        = "./modules/lambda_function_direct"
  function_name = "dev_bgg_generate_game_urls"
  timeout       = 900
  memory_size   = 1024
  role          = module.bgg_generate_game_urls_lambda_role.arn
  handler       = "generate_game_urls_lambda.lambda_handler"
  layers        = ["arn:aws:lambda:${var.REGION}:336392948345:layer:AWSSDKPandas-Python312:13"]
  environment   = "dev"
  description   = "DEV Lambda function to generate game urls"
}

module "bgg_generate_game_urls_lambda_role" {
  source    = "./modules/iam_lambda_roles"
  role_name = "bgg_generate_game_urls_lambda_role"
}
resource "aws_iam_role_policy_attachment" "bgg_generate_game_urls_lambda_role" {
  role       = module.bgg_generate_game_urls_lambda_role.role_name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

module "bgg_generate_user_urls" {
  source        = "./modules/lambda_function_direct"
  function_name = "bgg_generate_user_urls"
  timeout       = 900
  memory_size   = 1024
  role          = module.bgg_generate_user_urls_lambda_role.arn
  handler       = "generate_user_urls_lambda.lambda_handler"
  layers        = ["arn:aws:lambda:${var.REGION}:336392948345:layer:AWSSDKPandas-Python312:13"]
  environment   = "prod"
  description   = "Lambda function to generate user urls"
}

module "dev_bgg_generate_user_urls" {
  source        = "./modules/lambda_function_direct"
  function_name = "dev_bgg_generate_user_urls"
  timeout       = 900
  memory_size   = 1024
  role          = module.bgg_generate_user_urls_lambda_role.arn
  handler       = "generate_user_urls_lambda.lambda_handler"
  layers        = ["arn:aws:lambda:${var.REGION}:336392948345:layer:AWSSDKPandas-Python312:13"]
  environment   = "dev"
  description   = "DEV Lambda function to generate user urls"
}



module "bgg_generate_user_urls_lambda_role" {
  source    = "./modules/iam_lambda_roles"
  role_name = "bgg_generate_user_urls_lambda_role"
}


resource "aws_iam_role_policy_attachment" "bgg_generate_user_urls_lambda_role" {
  role       = module.bgg_generate_user_urls_lambda_role.role_name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

module "bgg_generate_ratings_urls" {
  source        = "./modules/lambda_function_direct"
  function_name = "bgg_generate_ratings_urls"
  timeout       = 900
  memory_size   = 1024
  role          = module.bgg_generate_ratings_urls_lambda_role.arn
  handler       = "generate_ratings_urls_lambda.lambda_handler"
  layers        = ["arn:aws:lambda:${var.REGION}:336392948345:layer:AWSSDKPandas-Python312:13"]
  environment   = "prod"
  description   = "Lambda function to generate ratings urls"
}
module "dev_bgg_generate_ratings_urls" {
  source        = "./modules/lambda_function_direct"
  function_name = "dev_bgg_generate_ratings_urls"
  timeout       = 900
  memory_size   = 1024
  role          = module.bgg_generate_ratings_urls_lambda_role.arn
  handler       = "generate_ratings_urls_lambda.lambda_handler"
  layers        = ["arn:aws:lambda:${var.REGION}:336392948345:layer:AWSSDKPandas-Python312:13"]
  environment   = "dev"
  description   = "DEV Lambda function to generate ratings urls"
}

module "trigger_bgg_generate_ratings_urls_lambda" {
  source        = "./modules/iam_lambda_run_permissions"
  function_name = module.bgg_generate_ratings_urls.function_name
  region        = var.REGION
  account_id    = data.aws_caller_identity.current.account_id
}

module "bgg_generate_ratings_urls_lambda_role" {
  source    = "./modules/iam_lambda_roles"
  role_name = "bgg_generate_ratings_urls_lambda"
}

resource "aws_iam_role_policy_attachment" "bgg_generate_ratings_urls_lambda_attach" {
  role       = module.bgg_generate_ratings_urls_lambda_role.role_name
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