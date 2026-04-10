# Root Terraform configuration for ECS Fargate app (Production-ready)

module "vpc" {
  source = "./modules/vpc"
  name   = var.vpc_name
  cidr   = var.vpc_cidr
  azs    = var.azs
  public_subnets  = var.public_subnets
  private_subnets = var.private_subnets
  tags = var.tags
}

module "iam" {
  source = "./modules/iam"
  app_name = var.app_name
  tags = var.tags
}

module "ecr" {
  source = "./modules/ecr"
  app_name = var.app_name
  tags = var.tags
}

module "cloudwatch" {
  source = "./modules/cloudwatch"
  app_name = var.app_name
  tags = var.tags
}

module "alb" {
  source = "./modules/alb"
  name   = var.alb_name
  vpc_id = module.vpc.vpc_id
  public_subnets = module.vpc.public_subnets
  container_port = var.container_port
  tags = var.tags
}

module "ecs" {
  source = "./modules/ecs"
  app_name = var.app_name
  cluster_name = var.ecs_cluster_name
  task_cpu = var.task_cpu
  task_memory = var.task_memory
  container_port = var.container_port
  image = module.ecr.repository_url
  execution_role_arn = module.iam.ecs_execution_role_arn
  log_group = module.cloudwatch.log_group_name
  log_region = var.region
  vpc_id = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnets
  alb_target_group_arn = module.alb.target_group_arn
  tags = var.tags
  alb_sg_id = module.alb.alb_sg_id
}

provider "aws" {
  region = var.region
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = ">= 2.0"
    }
  }
}