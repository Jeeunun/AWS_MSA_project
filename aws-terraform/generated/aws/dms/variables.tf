# RDS 서브넷 그룹 데이터 소스 (event-db 참조용)
data "aws_db_subnet_group" "rds_subnet_group" {
  name = "dugout-rds-subnet-group"
}

# RDS 보안 그룹 데이터 소스 (event-db 참조용)
data "aws_security_group" "rds_sg" {
  filter {
    name   = "group-name"
    values = ["RDS-SG"]
  }
}

# PRI 서브넷 데이터 소스 (DMS용)
data "aws_subnet" "pri_subnet_a" {
  filter {
    name   = "tag:Name"
    values = ["PRI-subnet-a"]
  }
}

data "aws_subnet" "pri_subnet_c" {
  filter {
    name   = "tag:Name"
    values = ["PRI-subnet-c"]
  }
}

# 기존 DMS 파라미터 그룹 데이터 소스
data "aws_db_parameter_group" "dms_pg" {
  name = "dms-pg"
}