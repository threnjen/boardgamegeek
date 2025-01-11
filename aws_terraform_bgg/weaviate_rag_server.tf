variable "weaviate_rag_server" {
  description = "The name of the ECS task definition for the weaviate_rag_server"
  type        = string
  default     = "weaviate_rag_server"
}

module "weaviate_rag_server_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = var.weaviate_rag_server
}