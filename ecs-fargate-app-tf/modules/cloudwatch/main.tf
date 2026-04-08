resource "aws_cloudwatch_log_group" "this" {
  name = "/ecs/${var.app_name}"
  retention_in_days = var.retention_in_days
  tags = var.tags
}

output "log_group_name" {
  value = aws_cloudwatch_log_group.this.name
}
