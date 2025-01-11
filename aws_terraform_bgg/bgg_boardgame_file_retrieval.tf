variable "bgg_boardgame_file_retrieval" {
  description = "The name of the ECS task definition for the bgg_boardgame_file_retrieval"
  type        = string
  default     = "bgg_boardgame_file_retrieval"
}

module "bgg_boardgame_file_retrieval_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = var.bgg_boardgame_file_retrieval
}

module "bgg_boardgame_file_retrieval_role" {
  source    = "./modules/iam_lambda_roles"
  role_name = "bgg_boardgame_file_retrieval_role"
}

resource "aws_iam_role_policy_attachment" "bgg_boardgame_file_retrieval_attach" {
  role       = module.bgg_boardgame_file_retrieval_role.role_name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

resource "aws_lambda_function" "bgg_boardgame_file_retrieval_lambda" {
  depends_on    = [module.bgg_boardgame_file_retrieval_ecr]
  function_name = var.bgg_boardgame_file_retrieval
  timeout       = 900
  memory_size   = 512
  image_uri     = "${module.bgg_boardgame_file_retrieval_ecr.repository_url}:latest"
  package_type  = "Image"
  description   = "Lambda function to retrieve the ranks csv from boardgamegeek"

  role = module.bgg_boardgame_file_retrieval_role.arn

  environment {
    variables = merge(
      {
        for tuple in regexall("(.*?)=(.*)", file("../.env")) : tuple[0] => tuple[1]
        if !(tuple[0] == "IS_LOCAL" || tuple[0] == "ENVIRONMENT" || tuple[0] == "PYTHONPATH")
      },
      {
        ENVIRONMENT = "prod"
    })
  }
}