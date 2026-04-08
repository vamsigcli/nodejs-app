terraform {
  backend "s3" {
    bucket         = "terraform-state-084250374231-ap-south-1-an"
    key            = "ecs-fargate-app/terraform.tfstate"
    region         = "ap-south-1"
    # S3 now supports native state locking (no DynamoDB required)
    # Optionally, you can enable encryption and versioning on the bucket for best practices
    # encrypt      = true
  }
}
