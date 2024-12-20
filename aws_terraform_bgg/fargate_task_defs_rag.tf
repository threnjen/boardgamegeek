resource "aws_ecs_task_definition" "dev_weaviate_rag_generation" {
  family = "dev_${var.rag_description_generation}"
  

  container_definitions = jsonencode([
    # {
    #   name      = "dev_${var.rag_description_generation}",
    #   image     = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/dev_${var.rag_description_generation}:latest"
    #   cpu       = 0,
    #   essential = true,
    #   environment = [
    #     {
    #       name  = "ENVIRONMENT",
    #       value = "prod"
    #     },
    #     {
    #       name  = "IS_LOCAL",
    #       value = "false"
    #     }
    #   ],
    #   environmentFiles = [
    #     {
    #       value = "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/boardgamegeek.env",
    #       type  = "s3"
    #     },
    #     {
    #       value = "arn:aws:s3:::${var.S3_SCRAPER_BUCKET}/weaviate.env",
    #       type  = "s3"
    #     }
    #   ],
    #   mountPoints = [],
    #   volumesFrom = [],
    #   ulimits     = [],
    #   logConfiguration = {
    #     logDriver = "awslogs",
    #     options = {
    #       "awslogs-group"         = "/ecs/dev_${var.rag_description_generation}",
    #       "awslogs-create-group"  = "true",
    #       "awslogs-region"        = var.REGION,
    #       "awslogs-stream-prefix" = "ecs"
    #     },
    #     secretOptions = []
    #   },
    #   systemControls = [],
    #   dependsOn = [
    #     {
    #       containerName = var.weaviate_rag_server,
    #       condition     = "START"
    #     }
    #   ]
    # },
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
        "--port", "8080",
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