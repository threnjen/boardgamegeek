variable "rag_description_generation" {
  description = "The name of the ECS task definition for the rag_description_generation"
  type        = string
  default     = "rag_description_generation"
}

module "rag_description_generation_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = var.rag_description_generation
}

module "dev_rag_description_generation_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = "dev_${var.rag_description_generation}"
}

module "rag_description_generation_FargateExecutionRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "${var.rag_description_generation}_FargateExecutionRole"
}

module "rag_description_generation_FargateTaskRole_role" {
  source          = "./modules/iam_ecs_roles"
  task_definition = "${var.rag_description_generation}_FargateTaskRole"
}

resource "aws_iam_role_policy_attachment" "S3_Access_rag_description_generation_FargateExecutionRole_attach" {
  role       = module.rag_description_generation_FargateExecutionRole_role.name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

resource "aws_iam_role_policy_attachment" "S3_Access_rag_description_generation_FargateTaskRole_attach" {
  role       = module.rag_description_generation_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

resource "aws_iam_role_policy_attachment" "Cloudwatch_Put_Metrics_rag_description_generation_FargateTaskRole_roleattach" {
  role       = module.rag_description_generation_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.Cloudwatch_Put_Metrics_policy.arn
}

resource "aws_iam_role_policy_attachment" "dynamodb_rag_description_generation_FargateTaskRole_roleattach" {
  role       = module.rag_description_generation_FargateTaskRole_role.name
  policy_arn = aws_iam_policy.game_generated_descriptions_dynamodb_access.arn
}

# not currently using EC2 for Weaviate server, but we'll keep this here for future use
# resource "aws_iam_role_policy_attachment" "rag_description_generation_SSM_send_command_attach" {
#   role       = module.rag_description_generation_FargateTaskRole_role.name
#   policy_arn = aws_iam_policy.SSM_send_command.arn
# }
# resource "aws_iam_role_policy_attachment" "ec2_instance_access_rag_description_generation_FargateTaskRole_roleattach" {
#   role       = module.rag_description_generation_FargateTaskRole_role.name
#   policy_arn = aws_iam_policy.ec2_instance_access.arn
# }

module "rag_description_generation" {
  source        = "./modules/lambda_function_direct"
  function_name = "rag_description_generation_fargate_trigger"
  timeout       = 900
  memory_size   = 256
  role          = module.rag_description_generation_role.arn
  handler       = "${var.rag_description_generation}_fargate_trigger.lambda_handler"
  layers        = ["arn:aws:lambda:${var.REGION}:336392948345:layer:AWSSDKPandas-Python312:13"]
  environment   = "prod"
  description   = "Lambda function to trigger the rag description generation fargate task"
}

module "dev_rag_description_generation" {
  source        = "./modules/lambda_function_direct"
  function_name = "dev_rag_description_generation_fargate_trigger"
  timeout       = 900
  memory_size   = 256
  role          = module.rag_description_generation_role.arn
  handler       = "${var.rag_description_generation}_fargate_trigger.lambda_handler"
  layers        = ["arn:aws:lambda:${var.REGION}:336392948345:layer:AWSSDKPandas-Python312:13"]
  environment   = "dev"
  description   = "DEV Lambda function to trigger the rag description generation fargate task"
}

module "rag_description_generation_role" {
  source    = "./modules/iam_lambda_roles"
  role_name = "rag_description_generation_retrieval_role"
}

resource "aws_iam_role_policy_attachment" "rag_description_generation_role_describe_attach" {
  role       = module.rag_description_generation_role.role_name
  policy_arn = module.rag_description_generation_describe_task_def_policy.lambda_ecs_trigger_arn
}

resource "aws_iam_role_policy_attachment" "rag_description_generation_attach" {
  role       = module.rag_description_generation_role.role_name
  policy_arn = aws_iam_policy.S3_Access_bgg_scraper_policy.arn
}

module "rag_description_generation_describe_task_def_policy" {
  source     = "./modules/lambda_ecs_trigger_policies"
  name       = "${var.rag_description_generation}_lambda_ecs_trigger"
  task_name  = var.rag_description_generation
  region     = var.REGION
  account_id = data.aws_caller_identity.current.account_id
}


resource "aws_ecs_task_definition" "weaviate_rag_generation" {
  family = var.rag_description_generation


  container_definitions = jsonencode([
    {
      name      = var.rag_description_generation,
      image     = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.rag_description_generation}:latest"
      cpu       = 0,
      essential = true,
      environment = [
        {
          name  = "ENVIRONMENT",
          value = "prod"
        },
        {
          name  = "IS_LOCAL",
          value = "false"
        }
      ],
      environmentFiles = [
        {
          value = "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/boardgamegeek.env",
          type  = "s3"
        },
        {
          value = "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/weaviate.env",
          type  = "s3"
        }
      ],
      mountPoints = [],
      volumesFrom = [],
      ulimits     = [],
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          "awslogs-group"         = "/ecs/${var.rag_description_generation}",
          "awslogs-create-group"  = "true",
          "awslogs-region"        = var.REGION,
          "awslogs-stream-prefix" = "ecs"
        },
        secretOptions = []
      },
      systemControls = [],
      dependsOn = [
        {
          containerName = var.weaviate_rag_server,
          condition     = "START"
        }
      ]
    },
    {
      name  = var.weaviate_rag_server,
      image = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.weaviate_rag_server}:latest"
      cpu   = 0,
      portMappings = [
        {
          containerPort = 8081,
          hostPort      = 8081
        },
        {
          containerPort = 50051,
          hostPort      = 50051
        },
      ],
      essential = true,
      environment = [
        {
          name  = "ENVIRONMENT",
          value = "prod"
        },
        {
          name  = "IS_LOCAL",
          value = "false"
        },
        {
          name  = "TRANSFORMERS_INFERENCE_API"
          value = "http://127.0.0.1:8080"
        }
      ],
      environmentFiles = [
        {
          value = "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/boardgamegeek.env",
          type  = "s3"
        },
        {
          value = "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/weaviate.env",
          type  = "s3"
        }
      ],
      command = [
        "--host", "0.0.0.0",
        "--port", "8081",
        "--scheme", "http"
      ],
      mountPoints = [],
      volumesFrom = [],
      ulimits     = [],
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          "awslogs-group"         = "/ecs/${var.weaviate_rag_server}",
          "awslogs-create-group"  = "true",
          "awslogs-region"        = var.REGION,
          "awslogs-stream-prefix" = "ecs"
        },
        secretOptions = []
      },
      systemControls = [],
      dependsOn = [
        {
          containerName = var.t2v-transformers,
          condition     = "START"
        }
      ]
    },
    {
      name      = var.t2v-transformers,
      image     = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.t2v-transformers}:latest"
      cpu       = 0,
      essential = true,
      environment = [
        {
          name  = "ENVIRONMENT",
          value = "prod"
        },
        {
          name  = "IS_LOCAL",
          value = "false"
        },
        {
          name  = "ENABLE_CUDA",
          value = "0"
      }],
      mountPoints = [],
      volumesFrom = [],
      ulimits     = [],
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          "awslogs-group"         = "/ecs/${var.t2v-transformers}",
          "awslogs-create-group"  = "true",
          "awslogs-region"        = var.REGION,
          "awslogs-stream-prefix" = "ecs"
        },
        secretOptions = []
      },
      systemControls = [],
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://127.0.0.1:8080/health || exit 1"],
        interval    = 30,
        retries     = 3,
        startPeriod = 60,
        timeout     = 5
      }
    },

    ],

  )

  task_role_arn      = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.rag_description_generation}_FargateTaskRole"
  execution_role_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.rag_description_generation}_FargateExecutionRole"

  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]

  cpu    = "2048"
  memory = "8192"

  runtime_platform {
    cpu_architecture        = "X86_64"
    operating_system_family = "LINUX"
  }
}

resource "aws_ecs_task_definition" "dev_weaviate_rag_generation" {
  family = "dev_${var.rag_description_generation}"


  container_definitions = jsonencode([
    {
      name      = "dev_${var.rag_description_generation}",
      image     = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/dev_${var.rag_description_generation}:latest"
      cpu       = 0,
      essential = true,
      environment = [
        {
          name  = "ENVIRONMENT",
          value = "prod"
        },
        {
          name  = "IS_LOCAL",
          value = "false"
        }
      ],
      environmentFiles = [
        {
          value = "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/boardgamegeek.env",
          type  = "s3"
        },
        {
          value = "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/weaviate.env",
          type  = "s3"
        }
      ],
      mountPoints = [],
      volumesFrom = [],
      ulimits     = [],
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          "awslogs-group"         = "/ecs/dev_${var.rag_description_generation}",
          "awslogs-create-group"  = "true",
          "awslogs-region"        = var.REGION,
          "awslogs-stream-prefix" = "ecs"
        },
        secretOptions = []
      },
      systemControls = [],
      dependsOn = [
        {
          containerName = var.weaviate_rag_server,
          condition     = "START"
        }
      ]
    },
    {
      name  = var.weaviate_rag_server,
      image = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.weaviate_rag_server}:latest"
      cpu   = 0,
      portMappings = [
        {
          containerPort = 8081,
          hostPort      = 8081
        },
        {
          containerPort = 50051,
          hostPort      = 50051
        },
      ],
      essential = true,
      environment = [
        {
          name  = "ENVIRONMENT",
          value = "prod"
        },
        {
          name  = "IS_LOCAL",
          value = "false"
        },
    {
      name  = "TRANSFORMERS_INFERENCE_API"
      value = "http://127.0.0.1:8080"
    }
      ],
      environmentFiles = [
        {
          value = "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/boardgamegeek.env",
          type  = "s3"
        },
        {
          value = "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/weaviate.env",
          type  = "s3"
        }
      ],
      command = [
        "--host", "0.0.0.0",
        "--port", "8081",
        "--scheme", "http"
      ],
      mountPoints = [],
      volumesFrom = [],
      ulimits     = [],
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          "awslogs-group"         = "/ecs/${var.weaviate_rag_server}",
          "awslogs-create-group"  = "true",
          "awslogs-region"        = var.REGION,
          "awslogs-stream-prefix" = "ecs"
        },
        secretOptions = []
      },
      systemControls = [],
  dependsOn = [
    {
      containerName = var.t2v-transformers,
      condition     = "START"
    }
  ]
    },
{
  name      = var.t2v-transformers,
  image     = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.t2v-transformers}:latest"
  cpu       = 0,
  essential = true,
  environment = [
    {
      name  = "ENVIRONMENT",
      value = "prod"
    },
    {
      name  = "IS_LOCAL",
      value = "false"
    },
    {
      name  = "ENABLE_CUDA",
      value = "0"
  }],
  mountPoints = [],
  volumesFrom = [],
  ulimits     = [],
  logConfiguration = {
    logDriver = "awslogs",
    options = {
      "awslogs-group"         = "/ecs/${var.t2v-transformers}",
      "awslogs-create-group"  = "true",
      "awslogs-region"        = var.REGION,
      "awslogs-stream-prefix" = "ecs"
    },
    secretOptions = []
  },
  systemControls = [],
  healthCheck = {
    command     = ["CMD-SHELL", "curl -f http://127.0.0.1:8080/health || exit 1"],
    interval    = 30,
    retries     = 3,
    startPeriod = 60,
    timeout     = 5
  }
},

    ],

  )

  task_role_arn      = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.rag_description_generation}_FargateTaskRole"
  execution_role_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.rag_description_generation}_FargateExecutionRole"

  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]

  cpu    = "2048"
  memory = "8192"

  runtime_platform {
    cpu_architecture        = "X86_64"
    operating_system_family = "LINUX"
  }
}

resource "aws_cloudwatch_log_group" "weaviate_rag_generation_log_group" {
  name = "/ecs/${var.rag_description_generation}"

  retention_in_days = 3
}

resource "aws_cloudwatch_log_group" "weaviate_rag_generation_dev_log_group" {
  name = "/ecs/dev_${var.rag_description_generation}"

  retention_in_days = 3
}

resource "aws_cloudwatch_log_group" "t2v-transformers_log_group" {
  name = "/ecs/${var.t2v-transformers}"

  retention_in_days = 3
}

resource "aws_cloudwatch_log_group" "weaviate_rag_server_log_group" {
  name = "/ecs/${var.weaviate_rag_server}"

  retention_in_days = 3
}


# resource "aws_service_discovery_private_dns_namespace" "t2v-transformers-dev" {
#   name        = "t2v-transformers-dev"
#   vpc         = module.vpc.vpc_id
#   description = "Private DNS namespace for ECS service discovery"
# }

# resource "aws_service_discovery_service" "transformers_service_dev" {
#   name         = "t2v-transformers-dev"
#   namespace_id = aws_service_discovery_private_dns_namespace.t2v-transformers-dev.id

#   dns_config {
#     namespace_id = aws_service_discovery_private_dns_namespace.t2v-transformers-dev.id
#     dns_records {
#       type = "A"
#       ttl  = 60
#     }
#   }
# }

# resource "aws_ecs_service" "transformers_service_dev" {
#   name            = "dev-bgg-weaviate-service"
#   cluster         = aws_ecs_cluster.boardgamegeek.id
#   task_definition = aws_ecs_task_definition.dev_weaviate_rag_generation.arn
#   desired_count   = 0
#   launch_type     = "FARGATE"

#   network_configuration {
#     subnets          = module.vpc.private_subnets
#     security_groups  = [aws_security_group.shared_resources_sg.id, aws_security_group.ec2_weaviate_port_access.id]
#     assign_public_ip = false
#   }

#   service_registries {
#     registry_arn = aws_service_discovery_service.transformers_service_dev.arn
#   }
# }