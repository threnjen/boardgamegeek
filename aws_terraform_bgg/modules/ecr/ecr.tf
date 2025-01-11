variable "ecr_repository_name" {
  description = "The name of the ECR repository"
  type        = string
}

output "ecr_repository_name" {
  value = aws_ecr_repository.ecr_repository.arn
}

resource "aws_ecr_repository" "ecr_repository" {
  name = var.ecr_repository_name
  image_scanning_configuration {
    scan_on_push = true
  }
  force_delete = true
}

resource "aws_ecr_lifecycle_policy" "lifecycle_policy" {
  depends_on = [ aws_ecr_repository.ecr_repository ]
  repository = var.ecr_repository_name

  policy = <<EOF
{
    "rules": [
        {
            "rulePriority": 1,
            "description": "Expire more than 1 images",
            "selection": {
                "tagStatus": "any",
                "countType": "imageCountMoreThan",
                "countNumber": 1
            },
            "action": {
                "type": "expire"
            }
        }
    ]
}
EOF
}

output "repository_url" {
  value = aws_ecr_repository.ecr_repository.repository_url
}