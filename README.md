# Node.js ECS Fargate Demo App

This project demonstrates a secure, production-ready CI/CD pipeline for deploying a containerized Node.js application to AWS ECS Fargate using modular Terraform and GitHub Actions.



---

## Architecture Overview

- **Node.js App**: Simple Express app served via ECS Fargate.
- **ECS Fargate**: Runs containers in private subnets for security.
- **Application Load Balancer (ALB)**: Publicly accessible, routes traffic to ECS tasks.
- **VPC**: Custom VPC with public subnets (for ALB) and private subnets (for ECS tasks).
- **ECR**: Stores Docker images.
- **IAM**: Fine-grained roles for ECS, ECR, and GitHub Actions OIDC.
- **CloudWatch**: Centralized logging and alarms for health monitoring.
- **GitHub Actions**: CI/CD pipeline with OIDC authentication to AWS.

---

## Getting Started

### 1. Prerequisites
- AWS CLI configured
- Terraform >= 1.0
- Docker
- Node.js & npm
- GitHub repository with OIDC setup (see below)

### 2. Infrastructure Setup

```sh
cd ecs-fargate-app-tf
terraform init
terraform apply
```
- This will provision VPC, subnets, ALB, ECS, ECR, IAM, and CloudWatch resources using modular Terraform code.
- **State files are git-ignored for security.**

### 3. Build & Push Docker Image (First Time)

```sh
cd node-js-app
# Authenticate Docker to ECR
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com
# Build and tag image
docker build -t <ecr-repo-name>:latest .
docker tag <ecr-repo-name>:latest <account-id>.dkr.ecr.<region>.amazonaws.com/<ecr-repo-name>:latest
# Push to ECR
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/<ecr-repo-name>:latest
```

### 4. CI/CD Pipeline
- On push to `main`, GitHub Actions will:
  - Lint and test the Node.js app
  - Build and push Docker image to ECR
  - Deploy to ECS using OIDC-authenticated AWS credentials

### 5. Accessing the Application
- Find the ALB DNS name from Terraform outputs or AWS Console.
- Visit `http://<alb-dns-name>/` to access the app.

---

## Security & Best Practices

- **Modular Terraform**: VPC, ALB, ECS, IAM, ECR, and CloudWatch are modular for reusability and clarity.
- **State File Security**: `.gitignore` includes Terraform state files to prevent secrets leakage.
- **Network Segmentation**: ECS tasks run in private subnets; ALB is in public subnets.
- **Least Privilege IAM**: Roles grant only required permissions for ECS, ECR, and CI/CD.
- **OIDC for GitHub Actions**: No static AWS keys; secure, short-lived credentials via OIDC.
- **Tight Firewalls**: Security groups allow only required traffic (ALB: 80/443 from internet, ECS: only from ALB).
- **Logging & Monitoring**: Centralized CloudWatch logs and alarms for ALB 5xx and ECS health.
- **CI/CD Quality Gates**: Linting and unit tests enforced in pipeline.

---

## Runbook & Operations
- **Rollback**: Update ECS task definition to previous image/tag and redeploy.
- **Alarms**: CloudWatch alarms notify on ALB 5xx errors and ECS unhealthy tasks.
- **Extensibility**: Add SNS/email notifications, blue/green deployments, or more tests as needed.

---

## OIDC Setup for GitHub Actions
1. Create OIDC provider and IAM role using Terraform (`oidc-github.tf`).
2. Update `github_repo` variable to match your repo.
3. In GitHub, set repository secrets for AWS account ID, region, and ECR repo if needed.

---



```
[User] ---> [ALB (Public Subnet)] ---> [ECS Service (Private Subnet)] ---> [ECR, CloudWatch, IAM]
```

---

## Contact & Contributions
Open issues or PRs for improvements, security suggestions, or questions.
