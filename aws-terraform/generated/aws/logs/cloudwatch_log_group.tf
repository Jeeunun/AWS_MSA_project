# CloudWatch Log Groups - 기존 리소스들을 데이터 소스로 참조

data "aws_cloudwatch_log_group" "rds_error" {
  name = "/aws/rds/instance/user-service-db/error"
}

data "aws_cloudwatch_log_group" "user_inspect_task" {
  name = "/ecs/User-Inspect-Task"
}

data "aws_cloudwatch_log_group" "board_task_migrate" {
  name = "/ecs/board-task-migrate"
}

data "aws_cloudwatch_log_group" "board_task_web" {
  name = "/ecs/board-task-web"
}

data "aws_cloudwatch_log_group" "event_task_crawl" {
  name = "/ecs/event-task-crawl"
}

data "aws_cloudwatch_log_group" "event_task_migrate" {
  name = "/ecs/event-task-migrate"
}

data "aws_cloudwatch_log_group" "event_task_web" {
  name = "/ecs/event-task-web"
}

data "aws_cloudwatch_log_group" "info_task" {
  name = "/ecs/info-tesk"
}

data "aws_cloudwatch_log_group" "mysql_login_check" {
  name = "/ecs/mysql-login-check"
}

data "aws_cloudwatch_log_group" "news_service_web" {
  name = "/ecs/news-service-web"
}

data "aws_cloudwatch_log_group" "news_task_crawl" {
  name = "/ecs/news-task-crawl"
}

data "aws_cloudwatch_log_group" "news_task_migrate" {
  name = "/ecs/news-task-migrate"
}

data "aws_cloudwatch_log_group" "test_news_task_crawl" {
  name = "/ecs/test-news-task-crawl"
}

data "aws_cloudwatch_log_group" "test_news_task_migrate" {
  name = "/ecs/test-news-task-migrate"
}

data "aws_cloudwatch_log_group" "test_news_task_web" {
  name = "/ecs/test-news-task-web"
}

data "aws_cloudwatch_log_group" "toolbox" {
  name = "/ecs/toolbox"
}

data "aws_cloudwatch_log_group" "user_task_migrate" {
  name = "/ecs/user-task-migrate"
}

data "aws_cloudwatch_log_group" "user_task_web" {
  name = "/ecs/user-task-web"
}

data "aws_cloudwatch_log_group" "rds_os_metrics" {
  name = "RDSOSMetrics"
}

data "aws_cloudwatch_log_group" "onprem_db_mysql_error" {
  name = "onprem/db/mysql-error"
}

data "aws_cloudwatch_log_group" "onprem_db_mysql_slow" {
  name = "onprem/db/mysql-slow"
}

data "aws_cloudwatch_log_group" "onprem_system_cloud_init" {
  name = "onprem/system/cloud-init"
}

data "aws_cloudwatch_log_group" "onprem_system_messages" {
  name = "onprem/system/messages"
}

data "aws_cloudwatch_log_group" "onprem_system_secure" {
  name = "onprem/system/secure"
}