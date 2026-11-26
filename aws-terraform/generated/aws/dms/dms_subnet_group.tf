# 새로운 DMS 서브넷 그룹 생성 (기존 것과 충돌 방지)
resource "aws_dms_replication_subnet_group" "event_dms_subnet_group_new" {
  replication_subnet_group_id          = "event-dms-subnet-group-new"
  replication_subnet_group_description = "DMS replication subnet group for event migration (new)"
  
  subnet_ids = [
    data.aws_subnet.rds_subnet_a.id,  # RDS-subnet-a
    data.aws_subnet.rds_subnet_c.id   # RDS-subnet-c
  ]

  tags = {
    Name = "Event-DMS-Subnet-Group-New"
  }
}