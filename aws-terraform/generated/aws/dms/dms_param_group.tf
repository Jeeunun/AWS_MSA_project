resource "aws_db_parameter_group" "dms-pg" {
  description = "dms-pg"
  family      = "mysql8.0"
  name        = "dms-pg"

  # binlog_expire_logs_seconds는 수정 불가능한 파라미터이므로 제거

  parameter {
    apply_method = "immediate"
    name         = "binlog_format"
    value        = "ROW"
  }

  parameter {
    apply_method = "immediate"
    name         = "binlog_row_image"
    value        = "full"
  }

  parameter {
    apply_method = "immediate"
    name         = "interactive_timeout"
    value        = "28800"
  }

  parameter {
    apply_method = "immediate"
    name         = "net_read_timeout"
    value        = "3600"
  }

  parameter {
    apply_method = "immediate"
    name         = "net_write_timeout"
    value        = "3600"
  }

  parameter {
    apply_method = "immediate"
    name         = "sql_mode"
    value        = "STRICT_TRANS_TABLES"
  }

  parameter {
    apply_method = "immediate"
    name         = "wait_timeout"
    value        = "28800"
  }

  region       = "ap-northeast-2"
  skip_destroy = "false"
}