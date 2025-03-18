variable "task_definition_family" {
  type = string
}

variable "task_definition_name" {
  type = string
}

variable "registry_name"{
    type = string
}

variable "environment" {
  type = string
}

variable "env_file" {
    type = string
}

variable "task_role_arn" {
  type = string
}

variable "execution_role_arn" {
  type = string
}

variable "cpu" {
  type = string
}

variable "memory" {
  type = string
}

variable "region" {
  type = string
}

variable "image" {
  type = string
}