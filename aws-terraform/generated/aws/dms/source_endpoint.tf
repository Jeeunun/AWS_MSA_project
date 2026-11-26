# DMS 소스 엔드포인트 (event-db 참조)
resource "aws_dms_endpoint" "dms_event_source" {
  endpoint_id                 = "dms-event-source"
  endpoint_type               = "source"
  engine_name                 = "mysql"
  
  # RDS 인스턴스 정보 (직접 참조)
  server_name                 = aws_db_instance.tfer--event-db.address
  port                        = aws_db_instance.tfer--event-db.port
  database_name               = aws_db_instance.tfer--event-db.db_name
  username                    = aws_db_instance.tfer--event-db.username
  password                    = aws_db_instance.tfer--event-db.password
  
  # 기본 설정
  ssl_mode                    = "none"
  extra_connection_attributes = ""
  
  tags = {
    Name = "DMS Event Source Endpoint"
  }
}