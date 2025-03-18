variable "t2v-transformers" {
  description = "The name of the ECS task definition for the t2v-transformers"
  type        = string
  default     = "t2v-transformers"
}

module "t2v-transformers_ecr" {
  source              = "./modules/ecr"
  ecr_repository_name = var.t2v-transformers
}