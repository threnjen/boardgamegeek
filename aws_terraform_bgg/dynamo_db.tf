resource "aws_dynamodb_table" "game_generated_descriptions-dynamodb-table" {
  name                        = "game_generated_descriptions"
  hash_key                    = "game_id"
  billing_mode                = "PAY_PER_REQUEST"
  deletion_protection_enabled = true

  attribute {
    name = "game_id"
    type = "S"
  }

  #   attribute {
  #     name = "game_description"
  #     type = "S"
  #   }

  #   attribute {
  #     name = "game_pros"
  #     type = "S"
  #   }

  #   attribute {
  #     name = "game_cons"
  #     type = "S"
  #   }

  tags = {
    Name        = "game_generated_descriptions"
    Environment = "production"
  }
}