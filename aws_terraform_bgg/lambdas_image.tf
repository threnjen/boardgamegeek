resource "aws_lambda_function" "bgg_boardgame_file_retrieval_lambda" {
  depends_on    = [module.bgg_boardgame_file_retrieval_ecr]
  function_name = "bgg_boardgame_file_retrieval"
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