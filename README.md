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

| Action | How |
|--------|-----|
| **Manual rollback** | `aws ecs update-service --cluster ecs-prod-cluster --service nodejs-app-service --task-definition nodejs-app:<N>` |
| **Check alarm state** | `aws cloudwatch describe-alarms --alarm-names ALB-5XX-Errors ECS-Running-Task-Count --no-cli-pager` |
| **View Lambda rollback logs** | AWS Console → CloudWatch → Log groups → `/aws/lambda/ecs-rollback-on-alarm` |
| **Test live app** | `curl http://<alb-dns>/` and `curl http://<alb-dns>/health` |
| **Extensibility** | Add HTTPS/ACM, blue/green CodeDeploy, or Slack webhook from SNS |

---

## OIDC Setup for GitHub Actions
1. Create OIDC provider and IAM role using Terraform (`oidc-github.tf`).
2. Update `github_repo` variable to match your repo.
3. In GitHub, set repository secrets for AWS account ID, region, and ECR repo if needed.

---


## CloudWatch Alarm-Triggered Automatic Rollback

We have implemented a fully automated rollback strategy that triggers when a CloudWatch alarm fires (e.g., ALB 5xx errors or ECS running task count drops). Here is the complete flow:

```
CloudWatch Alarm → SNS Topic → Lambda Function → ECS UpdateService (previous task definition)
```

### Components Implemented

| Component | Description |
|-----------|-------------|
| **CloudWatch Alarms** | Monitor ALB 5xx errors and ECS running task count |
| **SNS Topic** (`ecs-rollback-alerts`) | Receives alarm notifications |
| **Lambda Function** (`ecs-rollback-on-alarm`) | Subscribes to SNS, finds previous stable task definition, rolls back ECS service |
| **IAM Role** (`lambda-rollback-role`) | Grants Lambda permissions to describe/update ECS services |

### How It Works
1. A CloudWatch alarm fires (ALB 5xx errors or unhealthy ECS tasks detected).
2. The alarm sends a notification to the **SNS topic**.
3. **Lambda** is triggered by SNS. It:
   - Calls `ecs:DescribeServices` to get the current task definition family.
   - Calls `ecs:ListTaskDefinitions` (sorted DESC) to find the **previous stable revision**.
   - Calls `ecs:UpdateService` with `forceNewDeployment=true` to roll back.
4. ECS replaces running tasks with the previous stable version.
5. Lambda logs all actions to **CloudWatch Logs** (`/aws/lambda/ecs-rollback-on-alarm`).

### Terraform Resources
- `aws_sns_topic.ecs_rollback_alerts` — SNS topic wired to both alarms.
- `aws_lambda_function.ecs_rollback` — Lambda zipped from `lambda_rollback.py`.
- `aws_lambda_permission.allow_sns_invoke` — Allows SNS to invoke Lambda.
- `aws_sns_topic_subscription.lambda_rollback_sub` — Subscribes Lambda to SNS.
- `aws_iam_role.lambda_rollback_role` + `aws_iam_role_policy.lambda_rollback_policy` — Least-privilege IAM for Lambda.

---

## ECS Deployment Circuit Breaker (Automatic Rollback)

I have implemented automatic rollback for ECS deployments using the ECS deployment circuit breaker feature. This ensures that if a deployment fails—such as when new tasks become unhealthy or cannot start—ECS will automatically revert the service to the last stable version, minimizing downtime and manual intervention.

### How I Implemented Rollback
- The ECS service is configured in Terraform with the `deployment_circuit_breaker` block, setting `enable = true` and `rollback = true`.
- With this setup, ECS continuously monitors deployments. If a failure is detected, ECS triggers an automatic rollback to the previous stable task definition revision.
- This approach provides fast, reliable rollbacks and aligns with AWS best practices for resilient, production-grade deployments.

```
[User] ---> [ALB (Public Subnet)] ---> [ECS Service (Private Subnet)] ---> [ECR, CloudWatch, IAM]
```

---

## Contact & Contributions
Open issues or PRs for improvements, security suggestions, or questions...
