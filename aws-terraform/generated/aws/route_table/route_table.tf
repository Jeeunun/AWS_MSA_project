# VPN Gateway 데이터 소스
data "aws_vpn_gateway" "vgw" {
  filter {
    name   = "tag:Name"
    values = ["VGW-24"]
  }
}

# Public Route Table
resource "aws_route_table" "tfer--rtb-02e2b0e7d5ba0d441" {
  vpc_id = data.aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = data.aws_internet_gateway.main.id
  }

  tags = {
    Name = "PUB-RT"
  }
}

# Private Route Table
resource "aws_route_table" "tfer--rtb-03a439676c94e13f9" {
  vpc_id = data.aws_vpc.main.id

  route {
     cidr_block     = "0.0.0.0/0"
     nat_gateway_id = data.aws_nat_gateway.main.id
   }

  # VPN Gateway를 통한 온프레미스 네트워크 라우트
  route {
    cidr_block         = "192.168.0.0/16"
    gateway_id     = data.aws_vpn_gateway.vgw.id
  }

  tags = {
    Name = "PRI-RT"
  }
}

# VPN Route Table (RDS용)
resource "aws_route_table" "tfer--rtb-0ef557541f5e226ee" {
  vpc_id = data.aws_vpc.main.id

  # VPN Gateway를 통한 온프레미스 네트워크 라우트
  route {
    cidr_block         = "192.168.0.0/16"
    gateway_id     = data.aws_vpn_gateway.vgw.id
  }

  tags = {
    Name = "RDS-RT"
  }
}