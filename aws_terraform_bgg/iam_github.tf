

module "iam_github_oidc_provider" {
  source = "terraform-aws-modules/iam/aws//modules/iam-github-oidc-provider"
}

output "GitHubActions_Push_Role_arn" {
  value = aws_iam_role.GitHubActions_Push_Role_role.arn
}
resource "aws_iam_role" "GitHubActions_Push_Role_role" {
  name = "GitHubActions_Push_Role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          "Federated" : "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/token.actions.githubusercontent.com"
        },
        Action = "sts:AssumeRoleWithWebIdentity",
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" : "sts.amazonaws.com"
          },
          StringLike = {
            "token.actions.githubusercontent.com:sub" : "repo:${var.GITHUB_USER_NAME}/*"
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "boardgamegeekscraper_github_cicd_ecrGitHubActions_Push_Role_attach" {
  role       = aws_iam_role.GitHubActions_Push_Role_role.name
  policy_arn = aws_iam_policy.boardgamegeekscraper_github_cicd_ecr_policy.arn
}

resource "aws_iam_role_policy_attachment" "boardgamegeekscraper_github_cicd_lambda_functionsGitHubActions_Push_Role_attach" {
  role       = aws_iam_role.GitHubActions_Push_Role_role.name
  policy_arn = aws_iam_policy.boardgamegeekscraper_github_cicd_lambda_functions_policy.arn
}

resource "aws_iam_role_policy_attachment" "boardgamegeekscraper_github_cicd_s3_policyGitHubActions_Push_Role_attach" {
  role       = aws_iam_role.GitHubActions_Push_Role_role.name
  policy_arn = aws_iam_policy.boardgamegeekscraper_github_cicd_s3_policy.arn
}

resource "aws_iam_policy" "boardgamegeekscraper_github_cicd_s3_policy" {
  name = "boardgamegeekscraper_github_cicd_s3"
  path = "/"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "Statement1",
        Effect = "Allow",
        Action = [
          "s3:PutObject"
        ],
        Resource = ["*"]
      }
    ]
  })
}

resource "aws_iam_policy" "boardgamegeekscraper_github_cicd_lambda_functions_policy" {
  name = "boardgamegeekscraper_github_cicd_lambda_functions"
  path = "/"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "Statement1",
        Effect = "Allow",
        Action = [
          "iam:ListRoles"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "lambda:UpdateFunctionCode",
          "lambda:GetFunctionConfiguration",
          "lambda:UpdateFunctionConfiguration",
          "lambda:GetFunction"
        ],
        Resource = [
          for repo in local.lambda_functions : format("arn:aws:lambda:${var.REGION}:${data.aws_caller_identity.current.account_id}:function:%s", repo)
        ]
      }
    ]
  })
}

resource "aws_iam_policy" "boardgamegeekscraper_github_cicd_ecr_policy" {
  name = "boardgamegeekscraper_github_cicd_ecr"
  path = "/"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid      = "VisualEditor0",
        Effect   = "Allow",
        Action   = "ecr:GetAuthorizationToken",
        Resource = "*"
      },
      {
        Sid    = "VisualEditor1",
        Effect = "Allow",
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:CompleteLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:InitiateLayerUpload",
          "ecr:BatchCheckLayerAvailability",
          "ecr:PutImage"
        ],
        # Resource = [
        #   for repo in local.ecr_repositories : format("arn:aws:ecr:${var.REGION}:${data.aws_caller_identity.current.account_id}:repository/%s", repo)
        # ]
        Resource = [for repo in local.ecr_repositories : "${repo}"]
      }
    ]
  })
}