resource "aws_iam_policy" "S3_Access_bgg_scraper_policy" {
  name = "S3_Access_bgg_scraper"
  path = "/"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:ListBucket",
          "s3:PutObject",
          "s3:GetObject",
          "s3:GetObjectAttributes",
          "s3:DeleteObject"
        ]
        Effect = "Allow"
        Resource = [
          "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}",
          "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/*",
          "arn:aws:s3:::${var.BUCKET}",
          "arn:aws:s3:::${var.BUCKET}/*"
        ]
      },
      { Action = [
        "s3:ListAllMyBuckets"
        ]
        Effect = "Allow"
      Resource = "*" }
    ]
  })
}

resource "aws_iam_policy" "Cloudwatch_Put_Metrics_policy" {
  name = "Cloudwatch_Put_Metrics"
  path = "/"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "VisualEditor0",
        Effect = "Allow",
        Action = [
          "cloudwatch:PutMetricAlarm",
          "cloudwatch:PutMetricData"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_policy" "SSM_send_command" {
  name = "SSM_send_command"
  path = "/"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "VisualEditor0",
        Effect = "Allow",
        Action = [
          "ssm:SendCommand",
          "ssm:GetCommandInvocation"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_policy" "ec2_instance_access" {
  name = "ec2_instance_access"
  path = "/"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "VisualEditor0",
        Effect = "Allow",
        Action = [
          "ec2:StartInstances",
        ],
        Resource = "*"
      }
    ]
  })
}



resource "aws_iam_policy" "glue_table_access" {
  name        = "glue_access_permissions"
  description = "Policy to allow running access to Glue tables for BGG Scraper/Cleaner tasks"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid = "GlueTableAccess"
        Action = [
          "glue:CreateTable",
          "glue:GetTable",
          "glue:GetTables",
          "glue:UpdateTable",
          "glue:DeleteTable",
          "glue:BatchDeleteTable",
          "glue:GetTableVersion",
          "glue:GetTableVersions",
          "glue:DeleteTableVersion",
          "glue:BatchDeleteTableVersion",
          "glue:CreatePartition",
          "glue:BatchCreatePartition",
          "glue:GetPartition",
          "glue:GetPartitions",
          "glue:BatchGetPartition",
          "glue:UpdatePartition",
          "glue:DeletePartition",
          "glue:BatchDeletePartition"
        ]
        Effect = "Allow"
        Resource = [
          "arn:aws:glue:${var.REGION}:${data.aws_caller_identity.current.account_id}:catalog",
          "arn:aws:glue:${var.REGION}:${data.aws_caller_identity.current.account_id}:database/boardgamegeek",
          "arn:aws:glue:${var.REGION}:${data.aws_caller_identity.current.account_id}:table/boardgamegeek/*"

        ]
      },
    ]
  })
}