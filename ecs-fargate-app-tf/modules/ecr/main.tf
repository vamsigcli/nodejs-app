resource "aws_ecr_repository" "this" {
  name = var.app_name
  image_scanning_configuration {
    scan_on_push = true
  }
  tags = var.tags
}

output "repository_url" {
  value = aws_ecr_repository.this.repository_url
}
