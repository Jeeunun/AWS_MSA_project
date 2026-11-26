# VPC 데이터 소스
data "aws_vpc" "dugout_vpc" {
  filter {
    name   = "tag:Name"
    values = ["DugOut-VPC"]
  }
}

# DMS 보안 그룹 데이터 소스
data "aws_security_group" "dms_sg" {
  filter {
    name   = "group-name"
    values = ["DMS-SG"]
  }
}

# 기존 데이터 소스 제거 (새로운 서브넷 그룹 사용)

# DMS 복제 인스턴스
resource "aws_dms_replication_instance" "event_user_dms" {
  replication_instance_id     = "event-user-dms"
  replication_instance_class  = "dms.t3.medium"
  engine_version              = "3.5.3"
  allocated_storage           = 50
  
  # 네트워크 설정 (새로운 서브넷 그룹 사용)
  replication_subnet_group_id = aws_dms_replication_subnet_group.event_dms_subnet_group_new.id
  availability_zone           = "ap-northeast-2a"
  
  # 보안 그룹 참조
  vpc_security_group_ids = [
    data.aws_security_group.dms_sg.id
  ]
  
  # 기본 설정
  auto_minor_version_upgrade = true
  multi_az                   = false
  publicly_accessible        = false
  
  tags = {
    Name = "Event User DMS"
  }
}
