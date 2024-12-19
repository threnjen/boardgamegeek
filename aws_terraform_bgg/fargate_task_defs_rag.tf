resource "aws_ecs_task_definition" "weaviate_rag_generation" {
  family = var.rag_description_generation
  
  container_definitions = jsonencode([
    {
      name  = var.rag_description_generation,
      image = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.rag_description_generation}:latest"
      cpu   = 0,
      essential = true,
      environment = [
        {
          name  = "ENVIRONMENT",
          value = "prod"
        },
        {
          name = "IS_LOCAL",
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
      mountPoints  = [],
      volumesFrom  = [],
      ulimits      = [],
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
      systemControls = []
    },
    {
      name  = var.weaviate_rag_server,
      image = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.weaviate_rag_server}:latest"
      cpu   = 0,
      portMappings = [
        {
          containerPort = 8080,
          hostPort      = 8080
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
          name = "IS_LOCAL",
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
      command=[
        "--host", "0.0.0.0",
        "--port", "8080",
        "--scheme", "http"
      ],
      mountPoints  = [],
      volumesFrom  = [],
      ulimits      = [],
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
      systemControls = []
    },
    {
      name  = var.t2v-transformers,
      image = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.t2v-transformers}:latest"
      cpu   = 0,
      essential = true,
      environment = [
        {
          name  = "ENVIRONMENT",
          value = "prod"
        },
        {
          name = "IS_LOCAL",
          value = "false"
        },
        {
          name = "ENABLE_CUDA",
          value = "0"
        }],
      mountPoints  = [],
      volumesFrom  = [],
      ulimits      = [],
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
      systemControls = []
    },

  ])
  
  task_role_arn     = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.rag_description_generation}_FargateTaskRole"
  execution_role_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.rag_description_generation}_FargateExecutionRole"
  
  network_mode = "awsvpc"
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
      name  = var.rag_description_generation,
      image = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/dev_${var.rag_description_generation}:latest"
      cpu   = 0,
      essential = true,
      environment = [
        {
          name  = "ENVIRONMENT",
          value = "prod"
        },
        {
          name = "IS_LOCAL",
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
      mountPoints  = [],
      volumesFrom  = [],
      ulimits      = [],
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
      systemControls = []
    },
    {
      name  = var.weaviate_rag_server,
      image = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.weaviate_rag_server}:latest"
      cpu   = 0,
      portMappings = [
        {
          containerPort = 8080,
          hostPort      = 8080
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
          name = "IS_LOCAL",
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
      command=[
        "--host", "0.0.0.0",
        "--port", "8080",
        "--scheme", "http"
      ],
      mountPoints  = [],
      volumesFrom  = [],
      ulimits      = [],
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
      systemControls = []
    },
    {
      name  = var.t2v-transformers,
      image = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.REGION}.amazonaws.com/${var.t2v-transformers}:latest"
      cpu   = 0,
      essential = true,
      environment = [
        {
          name  = "ENVIRONMENT",
          value = "prod"
        },
        {
          name = "IS_LOCAL",
          value = "false"
        },
        {
          name = "ENABLE_CUDA",
          value = "0"
        }],
      mountPoints  = [],
      volumesFrom  = [],
      ulimits      = [],
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
      systemControls = []
    },

  ])
  
  task_role_arn     = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.rag_description_generation}_FargateTaskRole"
  execution_role_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.rag_description_generation}_FargateExecutionRole"
  
  network_mode = "awsvpc"
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