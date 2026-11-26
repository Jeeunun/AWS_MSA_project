# VPC 데이터 소스
data "aws_vpc" "main" {
  filter {
    name   = "tag:Name"
    values = ["DugOut-VPC"]
  }
}

# Internet Gateway 데이터 소스
data "aws_internet_gateway" "main" {
  filter {
    name   = "attachment.vpc-id"
    values = [data.aws_vpc.main.id]
  }
}

 # NAT Gateway 데이터 소스
 data "aws_nat_gateway" "main" {
   filter {
     name   = "vpc-id"
     values = [data.aws_vpc.main.id]
   }
 }
