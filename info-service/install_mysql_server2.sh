#!/bin/bash

# 서버 2 (MySQL 전용 서버) 설치 스크립트
# Ubuntu 24.04 환경용

# set -e 제거 (오류 발생 시에도 계속 진행)

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 로그 함수들
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { 
    echo ""
    echo "=================================="
    echo "STEP: $1"
    echo "=================================="
    echo ""
}

# 시스템 업데이트
log_step "시스템 업데이트"
log_info "시스템 패키지 업데이트 중..."
sudo apt update && sudo apt upgrade -y
log_info "시스템 업데이트 완료"

# MySQL 8.0 설치
log_step "MySQL 8.0 설치"
log_info "MySQL 8.0 설치 중..."
sudo apt install mysql-server-8.0 -y
log_info "MySQL 8.0 설치 완료"

# MySQL 서비스 시작 및 활성화
log_step "MySQL 서비스 설정"
log_info "MySQL 서비스 시작 중..."
sudo systemctl start mysql
sudo systemctl enable mysql
log_info "MySQL 서비스 상태 확인 중..."
sudo systemctl status mysql --no-pager

# MySQL 보안 초기 설정 (자동화)
log_step "MySQL 보안 설정"
log_info "MySQL 보안 설정을 자동으로 진행합니다..."

# MySQL 8.0의 인증 방식 문제 해결을 위한 단계별 설정
log_info "1단계: MySQL에 root로 접속하여 보안 설정..."

# 먼저 sudo mysql로 접속하여 root 비밀번호 설정
sudo mysql -u root << 'EOF'
-- 익명 사용자 제거
DELETE FROM mysql.user WHERE User='';

-- root 사용자 비밀번호 설정 (기본: root123)
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'root123';

-- test 데이터베이스 제거
DROP DATABASE IF EXISTS test;

-- 권한 테이블 새로고침
FLUSH PRIVILEGES;

-- 확인
SELECT User, Host FROM mysql.user WHERE User='root';
SHOW DATABASES;
EOF

log_info "MySQL 보안 설정 완료 (root 비밀번호: root123)"

# KBO 데이터베이스 및 사용자 생성
log_step "KBO 데이터베이스 및 사용자 생성"
log_info "MySQL에 root로 접속하여 데이터베이스 설정 중..."

# 임시 SQL 스크립트 생성
cat > /tmp/setup_kbo.sql << 'EOF'
-- 데이터베이스 생성 (이미 존재하면 무시)
CREATE DATABASE IF NOT EXISTS kbo_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 사용자 생성 (이미 존재하면 무시) - 모든 호스트에서 접근 가능
CREATE USER IF NOT EXISTS 'kbo_user'@'localhost' IDENTIFIED BY 'test';
CREATE USER IF NOT EXISTS 'kbo_user'@'%' IDENTIFIED BY 'test';

-- 권한 부여
GRANT ALL PRIVILEGES ON kbo_db.* TO 'kbo_user'@'localhost';
GRANT ALL PRIVILEGES ON kbo_db.* TO 'kbo_user'@'%';

-- 권한 테이블 새로고침
FLUSH PRIVILEGES;

-- 확인
SHOW DATABASES;
SELECT User, Host FROM mysql.user WHERE User='kbo_user';
EOF

# SQL 스크립트 실행 (이제 root 비밀번호 사용)
log_info "SQL 스크립트 실행 중..."
if sudo mysql -u root -proot123 < /tmp/setup_kbo.sql; then
    log_info "SQL 스크립트 실행 성공"
else
    log_error "SQL 스크립트 실행 실패"
    log_warning "수동으로 설정을 진행합니다..."
    
    # 수동 설정 안내
    log_info "MySQL에 root로 접속하여 수동 설정을 진행하세요:"
    echo ""
    echo "=== 수동 설정 명령어 ==="
    echo "sudo mysql -u root -proot123"
    echo ""
    echo "MySQL 프롬프트에서:"
    echo "CREATE DATABASE IF NOT EXISTS kbo_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    echo "CREATE USER IF NOT EXISTS 'kbo_user'@'localhost' IDENTIFIED BY 'test';"
    echo "CREATE USER IF NOT EXISTS 'kbo_user'@'%' IDENTIFIED BY 'test';"
    echo "GRANT ALL PRIVILEGES ON kbo_db.* TO 'kbo_user'@'localhost';"
    echo "GRANT ALL PRIVILEGES ON kbo_db.* TO 'kbo_user'@'%';"
    echo "FLUSH PRIVILEGES;"
    echo "EXIT;"
    echo "========================"
    echo ""
    
    read -p "수동 설정 완료 후 Enter를 누르세요..."
fi

# 임시 파일 정리
rm /tmp/setup_kbo.sql

# MySQL 원격 접속 허용 설정
log_step "MySQL 원격 접속 설정"
log_info "MySQL 설정 파일 수정 중..."

# MySQL 설정 파일 백업
sudo cp /etc/mysql/mysql.conf.d/mysqld.cnf /etc/mysql/mysql.conf.d/mysqld.cnf.backup

# bind-address 주석 처리 (원격 접속 허용)
sudo sed -i 's/^bind-address/#bind-address/' /etc/mysql/mysql.conf.d/mysqld.cnf

# MySQL 재시작
log_info "MySQL 재시작 중..."
sudo systemctl restart mysql

# MySQL 서비스 상태 확인
log_info "MySQL 서비스 상태 확인:"
sudo systemctl status mysql --no-pager

# 방화벽 설정
log_step "방화벽 설정"
log_info "방화벽 설정 중..."
sudo ufw enable
sudo ufw allow 22
sudo ufw allow 3306
sudo ufw status

# MySQL 연결 테스트
log_step "MySQL 연결 테스트"
log_info "로컬 MySQL 연결 테스트 중..."

if mysql -u kbo_user -ptest -e "SELECT 'Local connection successful' as status;" 2>/dev/null; then
    log_info "로컬 MySQL 연결 테스트 성공!"
else
    log_error "로컬 MySQL 연결 테스트 실패!"
    exit 1
fi

# 외부 접속 테스트를 위한 정보 출력
log_info "외부 접속 테스트를 위한 정보:"
log_info "MySQL 서버 IP: $(hostname -I | awk '{print $1}')"
log_info "MySQL 포트: 3306"
log_info "데이터베이스: kbo_db"
log_info "사용자: kbo_user"
log_info "비밀번호: test"

# MySQL 성능 튜닝 설정
log_step "MySQL 성능 튜닝"
log_info "MySQL 성능 튜닝 설정 중..."

# MySQL 설정 파일에 성능 튜닝 추가
sudo tee -a /etc/mysql/mysql.conf.d/mysqld.cnf > /dev/null << 'EOF'

# 성능 튜닝 설정
[mysqld]
# InnoDB 설정
innodb_buffer_pool_size = 256M
innodb_log_file_size = 64M
innodb_flush_log_at_trx_commit = 2
innodb_flush_method = O_DIRECT

# 연결 설정
max_connections = 200
max_connect_errors = 1000

# 쿼리 캐시 (MySQL 8.0에서는 제거됨)
# query_cache_size = 32M
# query_cache_type = 1

# 로그 설정
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 2

# 기타 설정
tmp_table_size = 64M
max_heap_table_size = 64M
table_open_cache = 2000
EOF

# MySQL 재시작
log_info "MySQL 재시작 중..."
sudo systemctl restart mysql

# MySQL 서비스 상태 확인
log_info "MySQL 서비스 상태 확인:"
sudo systemctl status mysql --no-pager

# 최종 확인
log_step "설치 완료 확인"
log_info "MySQL 서비스 상태:"
sudo systemctl status mysql --no-pager

log_info "방화벽 상태:"
sudo ufw status

echo ""
log_info "=================================="
log_info "서버 2 MySQL 설치 완료!"
log_info "=================================="
log_info "MySQL 서버 IP: $(hostname -I | awk '{print $1}')"
log_info "MySQL 포트: 3306"
log_info "데이터베이스: kbo_db"
log_info "사용자: kbo_user"
log_info "비밀번호: test"
log_info "root 비밀번호: root123"
echo ""
log_warning "서버 1에서 이 IP로 연결할 수 있도록 방화벽이 설정되었습니다."
log_warning "외부 접속 테스트: mysql -h $(hostname -I | awk '{print $1}') -u kbo_user -ptest kbo_db"
echo ""
log_info "테스트 명령어:"
log_info "mysql -u kbo_user -ptest kbo_db -e 'SHOW TABLES;'"
