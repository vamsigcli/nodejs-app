variable "name" { type = string }
variable "vpc_id" { type = string }
variable "public_subnets" { type = list(string) }
variable "container_port" { type = number }
variable "tags" {
  type = map(string)
  default = {}
}
