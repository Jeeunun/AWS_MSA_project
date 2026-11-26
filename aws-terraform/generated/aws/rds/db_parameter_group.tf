resource "aws_db_parameter_group" "main_rds_pg" {
  description = "Main RDS parameter group with DMS-compatible settings"
  family      = "mysql8.0"
  name        = "main-rds-pg"


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

  tags = {
    Name        = "Main-RDS-Parameter-Group"
    Environment = "production"
    Project     = "dugout"
  }
}

# DMS 전용 파라미터그룹 (event_db용)
resource "aws_db_parameter_group" "dms_pg" {
  description = "DMS-compatible parameter group for event_db"
  family      = "mysql8.0"
  name        = "dms-pg"


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

  tags = {
    Name        = "DMS-Parameter-Group"
    Environment = "production"
    Project     = "dugout"
    Purpose     = "DMS-migration"
  }
}
