resource "aws_ecs_task_definition" "task_definition" {
  family = var.task_definition_family
  
  container_definitions = jsonencode([
    {
      name  = var.task_definition_name,
      image = var.image
      cpu   = 0,
      portMappings = [
        {
          containerPort = 80,
          hostPort      = 80
        }
      ],
      essential = true,
      environment = [
        {
          name  = "ENV",
          value = var.environment
        }
      ],
      environmentFiles = [
        {
          value = var.env_file,
          type  = "s3"
        }
      ],
      mountPoints  = [],
      volumesFrom  = [],
      ulimits      = [],
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          "awslogs-group"         = "/ecs/${var.task_definition_name}",
          "awslogs-create-group"  = "true",
          "awslogs-region"        = var.region,
          "awslogs-stream-prefix" = "ecs"
        },
        secretOptions = []
      },
      systemControls = []
    },
    {
      name  = "aws-otel-collector",
      image = "public.ecr.aws/aws-observability/aws-otel-collector:v0.40.1",
      cpu   = 0,
      portMappings = [],
      essential    = true,
      command      = [
        "--config=/etc/ecs/ecs-cloudwatch.yaml"
      ],
      environment    = [],
      mountPoints    = [],
      volumesFrom    = [],
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          "awslogs-group"         = "/ecs/ecs-aws-otel-sidecar-collector",
          "awslogs-create-group"  = "true",
          "awslogs-region"        = var.region,
          "awslogs-stream-prefix" = "ecs"
        },
        secretOptions = []
      },
      systemControls = []
    }
  ])
  
  task_role_arn     = var.task_role_arn
  execution_role_arn = var.execution_role_arn
  
  network_mode = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  
  cpu    = var.cpu
  memory = var.memory
  
  runtime_platform {
    cpu_architecture        = "X86_64"
    operating_system_family = "LINUX"
  }
}