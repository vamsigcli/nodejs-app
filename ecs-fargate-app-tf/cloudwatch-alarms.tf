# -------------------------------------------------------
# SNS Topic for CloudWatch Alarm → Lambda Rollback
# -------------------------------------------------------
resource "aws_sns_topic" "ecs_rollback_alerts" {
  name = "ecs-rollback-alerts"
}

# -------------------------------------------------------
# SNS Topic for Email Notifications (team alerts)
# -------------------------------------------------------
resource "aws_sns_topic" "ecs_notifications" {
  name = "ecs-deployment-notifications"
}

resource "aws_sns_topic_subscription" "email_alert" {
  topic_arn = aws_sns_topic.ecs_notifications.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# -------------------------------------------------------
# Lambda function: auto-rollback ECS on alarm
# -------------------------------------------------------
data "archive_file" "lambda_rollback_zip" {
  type        = "zip"
  source_file = "${path.module}/lambda_rollback.py"
  output_path = "${path.module}/lambda_rollback.zip"
}

resource "aws_lambda_function" "ecs_rollback" {
  function_name    = "ecs-rollback-on-alarm"
  role             = module.iam.lambda_rollback_role_arn
  handler          = "lambda_rollback.lambda_handler"
  runtime          = "python3.12"
  filename         = data.archive_file.lambda_rollback_zip.output_path
  source_code_hash = data.archive_file.lambda_rollback_zip.output_base64sha256
  timeout          = 30

  environment {
    variables = {
      ECS_CLUSTER            = var.ecs_cluster_name
      ECS_SERVICE            = var.ecs_service_name
      NOTIFICATION_TOPIC_ARN = aws_sns_topic.ecs_notifications.arn
    }
  }

  tags = var.tags
}

# Allow SNS to invoke the Lambda function
resource "aws_lambda_permission" "allow_sns_invoke" {
  statement_id  = "AllowSNSInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ecs_rollback.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.ecs_rollback_alerts.arn
}

# Subscribe Lambda to SNS topic
resource "aws_sns_topic_subscription" "lambda_rollback_sub" {
  topic_arn = aws_sns_topic.ecs_rollback_alerts.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.ecs_rollback.arn
}

# -------------------------------------------------------
# CloudWatch Alarms — wired to SNS rollback topic
# -------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "alb_5xx_errors" {
  alarm_name          = "ALB-5XX-Errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Sum"
  threshold           = 1
  alarm_description   = "Alarm if ALB returns 5xx errors — triggers ECS rollback via Lambda."
  alarm_actions       = [aws_sns_topic.ecs_rollback_alerts.arn]
  ok_actions          = [aws_sns_topic.ecs_rollback_alerts.arn]
  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }
  treat_missing_data = "notBreaching"
}

resource "aws_cloudwatch_metric_alarm" "ecs_task_health" {
  alarm_name          = "ECS-Running-Task-Count"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 3
  metric_name         = "RunningTaskCount"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 1
  alarm_description   = "Alarm if ECS running tasks drops below 1 — triggers ECS rollback via Lambda."
  alarm_actions       = [aws_sns_topic.ecs_rollback_alerts.arn]
  ok_actions          = [aws_sns_topic.ecs_rollback_alerts.arn]
  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = var.ecs_service_name
  }
  treat_missing_data = "notBreaching"
}
