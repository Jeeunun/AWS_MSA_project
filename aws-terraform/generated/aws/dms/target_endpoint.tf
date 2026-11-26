# DMS 대상 엔드포인트 (외부 MySQL 서버)
resource "aws_dms_endpoint" "dms_user_target" {
  endpoint_id                 = "dms-user-target"
  endpoint_type               = "target"
  engine_name                 = "mysql"
  
  # 외부 MySQL 서버 정보
  server_name                 = "192.168.20.180"
  port                        = 3306
  username                    = "ecs_svc"
  password                    = "Qwert12345!?"
  
  # 기본 설정
  ssl_mode                    = "none"
  extra_connection_attributes = ""
  
  tags = {
    Name = "DMS User Target Endpoint"
  }
}
