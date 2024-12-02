data "aws_iam_policy_document" "assume_role_ecs" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
  
}
output "name" {
  value = aws_iam_role.fargate_task_definition.name
}

resource "aws_iam_role" "fargate_task_definition" {
  name = var.task_definition
  assume_role_policy = data.aws_iam_policy_document.assume_role_ecs.json
}

resource "aws_iam_role_policy_attachment" "AmazonEC2ContainerServiceRole_FargateExecutionRole" {
  role       = aws_iam_role.fargate_task_definition.name
  policy_arn = var.AmazonEC2ContainerServiceRole
}

resource "aws_iam_role_policy_attachment" "AWSAppRunnerServicePolicyForECRAccess_FargateExecutionRole" {
  role       = aws_iam_role.fargate_task_definition.name
  policy_arn = var.AWSAppRunnerServicePolicyForECRAccess
}

resource "aws_iam_role_policy_attachment" "CloudWatchFullAccessV2_FargateExecutionRole" {
  role       = aws_iam_role.fargate_task_definition.name
  policy_arn = var.CloudWatchFullAccessV2
}