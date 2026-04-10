variable "region" {
  description = "AWS region to deploy resources in."
  type        = string
  default     = "ap-south-1"
}

variable "vpc_name" {
  description = "Name for the VPC."
  type        = string
  default     = "ecs-prod-vpc"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "azs" {
  description = "List of availability zones."
  type        = list(string)
  default     = ["ap-south-1a", "ap-south-1b"]
}

variable "public_subnets" {
  description = "List of public subnet CIDRs."
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnets" {
  description = "List of private subnet CIDRs."
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
}

variable "tags" {
  description = "Map of tags to apply to resources."
  type        = map(string)
  default     = {
    Environment = "production"
    Project     = "ecs-fargate-app"
  }
}

variable "app_name" {
  description = "Name of the application."
  type        = string
  default     = "nodejs-app"
}

variable "ecs_cluster_name" {
  description = "Name of the ECS cluster."
  type        = string
  default     = "ecs-prod-cluster"
}

variable "task_cpu" {
  description = "CPU units for the ECS task."
  type        = string
  default     = "256"
}

variable "task_memory" {
  description = "Memory (MB) for the ECS task."
  type        = string
  default     = "512"
}

variable "container_port" {
  description = "Port the application container listens on."
  type        = number
  default     = 3000
}

variable "alb_name" {
  description = "Name for the Application Load Balancer."
  type        = string
  default     = "ecs-prod-alb"
}

variable "github_repo" {
  description = "GitHub repository in the format owner/repo (e.g., vamsi/nodejs-app)"
  type        = string
  default     = "vamsigcli/nodejs-app"
}

variable "alb_arn_suffix" {
  description = "The ARN suffix of the ALB (for CloudWatch alarm dimension)."
  type        = string
  default     = "app/ecs-prod-alb/98847c87d51ce522"
}

variable "ecs_service_name" {
  description = "The name of the ECS service (for CloudWatch alarm dimension)."
  type        = string
  default     = "nodejs-app-service"
}

variable "alert_email" {
  description = "Email address to receive ECS rollback and alarm notifications."
  type        = string
  default     = "vamsigcli@gmail.com"
}