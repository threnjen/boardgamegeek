resource "aws_ecs_cluster" "boardgamegeek" {
  name = "boardgamegeek"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}
