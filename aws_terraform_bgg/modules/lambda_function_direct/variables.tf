# Add any necessary variables in here
variable "function_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "role" {
  type = string
}

variable "handler" {
  type = string
}

variable "memory_size" {
  type = number
}

variable "timeout" {
  type = number
}

variable "layers" {
  type = list(string)
  default = []
}

variable "description" {
  type = string
  default = ""
}