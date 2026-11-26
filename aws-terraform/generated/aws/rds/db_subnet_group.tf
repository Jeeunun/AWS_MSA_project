# VPC 데이터 소스
data "aws_vpc" "main" {
  filter {
    name   = "tag:Name"
    values = ["DugOut-VPC"]
  }
}

# RDS 서브넷만 찾기 (이름에 RDS가 포함된 서브넷)
data "aws_subnets" "rds_subnets" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }
  
  filter {
    name   = "tag:Name"
    values = ["*RDS*"]
  }
}

# RDS용 서브넷들 (RDS 서브넷)
data "aws_subnet" "rds_subnet_a" {
  id = data.aws_subnets.rds_subnets.ids[0]
}

data "aws_subnet" "rds_subnet_c" {
  id = data.aws_subnets.rds_subnets.ids[1]
}

# DMS용 서브넷들 (RDS 서브넷과 동일)
data "aws_subnet" "pri_subnet_a" {
  id = data.aws_subnets.rds_subnets.ids[0]
}

data "aws_subnet" "pri_subnet_c" {
  id = data.aws_subnets.rds_subnets.ids[1]
}

# 통합 RDS Subnet Group (모든 RDS 인스턴스가 사용)
resource "aws_db_subnet_group" "main_rds_subnet_group" {
  name       = "dugout-rds-subnet-group"
  subnet_ids = [
    data.aws_subnet.rds_subnet_a.id,  # RDS-subnet-a
    data.aws_subnet.rds_subnet_c.id   # RDS-subnet-c
  ]

  tags = {
    Name = "DugOut-RDS-Subnet-Group"
  }
}
# DMS 전용 서브넷그룹 (event_db용)
resource "aws_db_subnet_group" "dms_subnet_group" {
  name       = "event-dms-subnet-group"
  subnet_ids = [
    data.aws_subnet.rds_subnet_a.id,  # RDS-subnet-a
    data.aws_subnet.rds_subnet_c.id   # RDS-subnet-c
  ]
  tags = {
    Name      = "Event-DMS-Subnet-Group-New"
    "aws:dms:rds-db-instance:repl-subnet-group" = "true"
    Environment = "production"
    Project     = "dugout"
    Purpose     = "DMS-migration"
  }
}

