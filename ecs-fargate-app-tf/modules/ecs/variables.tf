variable "app_name" { type = string }
variable "cluster_name" { type = string }
variable "task_cpu" { type = string }
variable "task_memory" { type = string }
variable "container_port" { type = number }
variable "image" { type = string }
variable "execution_role_arn" { type = string }
variable "log_group" { type = string }
variable "log_region" { type = string }
variable "vpc_id" { type = string }
variable "private_subnets" { type = list(string) }
variable "alb_target_group_arn" { type = string }
variable "tags" {
  type = map(string)
  default = {}
}
variable "desired_count" {
  type = number
  default = 2
}
variable "secrets" {
  type = map(string)
  default = {}
  description = "Map of secret environment variable names to Secrets Manager ARNs."
}
variable "alb_sg_id" {
  type = string
  default = ""
}
