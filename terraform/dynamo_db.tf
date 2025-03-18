resource "aws_dynamodb_table" "game_generated_descriptions-dynamodb-table" {
  name                        = "game_generated_descriptions"
  hash_key                    = "game_id"
  billing_mode                = "PAY_PER_REQUEST"
  deletion_protection_enabled = true

  attribute {
    name = "game_id"
    type = "S"
  }

  tags = {
    Name        = "game_generated_descriptions"
    Environment = "production"
  }
}

resource "aws_iam_policy" "game_generated_descriptions_dynamodb_access" {
  name = "game_generated_descriptions_dynamodb_access"
  path = "/"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "ListAllTables",
        Effect = "Allow",
        Action = [
          "dynamodb:ListTables",
        ],
        Resource = "*"
      },
      {
        Sid    = "PutGetItems",
        Effect = "Allow",
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem"
        ],
        Resource = [
          aws_dynamodb_table.game_generated_descriptions-dynamodb-table.arn
        ]
      }
    ]
  })
}

