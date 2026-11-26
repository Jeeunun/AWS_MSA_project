#!/bin/bash

# 서버 1 (Django + 크롤링 서버) 설치 스크립트
# Ubuntu 24.04 환경용

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# 서버 2 IP 입력 받기
log_step "서버 2 MySQL 연결 정보 입력"
echo "서버 2의 IP 주소를 입력해주세요:"
read -p "MySQL 서버 IP: " MYSQL_SERVER_IP

if [[ -z "$MYSQL_SERVER_IP" ]]; then
    log_error "IP 주소를 입력해주세요!"
    exit 1
fi

log_info "서버 2 IP: $MYSQL_SERVER_IP"

# 시스템 업데이트
log_step "시스템 업데이트"
log_info "시스템 패키지 업데이트 중..."
sudo apt update && sudo apt upgrade -y
log_info "시스템 업데이트 완료"

# Python 3.13 설치 (deadsnakes PPA 사용)
log_step "Python 3.13 설치"
log_info "deadsnakes PPA 추가 중..."
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
log_info "Python 3.13 설치 중..."
sudo apt install -y python3.13 python3.13-venv python3.13-dev
log_info "Python 3.13 설치 완료"

# pip가 없으면 자동 설치
log_info "pip 설치 확인 중..."
if ! python3.13 -m pip --version >/dev/null 2>&1; then
    log_info "pip 자동 설치 중..."
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.13
    log_info "pip 설치 완료"
fi

# Python 버전 확인
log_info "Python 버전 확인:"
python3.13 --version

# 필수 시스템 패키지 설치
log_step "시스템 패키지 설치"
log_info "필수 시스템 패키지 설치 중..."
sudo apt install -y unzip wget tar rsync curl build-essential
sudo apt install -y libxml2-dev libxslt-dev libmysqlclient-dev
sudo apt install -y nginx supervisor
log_info "시스템 패키지 설치 완료"

# Chrome 및 ChromeDriver 설치
log_step "Chrome 및 ChromeDriver 설치"
log_info "Chrome 설치 중..."

# Google Chrome 저장소 추가 및 설치
if ! command -v google-chrome &> /dev/null; then
    log_info "Google Chrome 저장소 추가 중..."
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
    sudo apt update
    
    log_info "Google Chrome 설치 중..."
    sudo apt install -y google-chrome-stable
else
    log_info "Google Chrome이 이미 설치되어 있습니다."
fi

# Chrome 버전 확인
CHROME_VERSION=$(google-chrome --version | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+' | head -1)
log_info "Chrome 버전: $CHROME_VERSION"

log_info "ChromeDriver 설치 중..."
# 기존 ChromeDriver가 있다면 제거
if [[ -f "/usr/local/bin/chromedriver" ]]; then
    log_info "기존 ChromeDriver 제거 중..."
    sudo rm /usr/local/bin/chromedriver
fi

cd /tmp

# Chrome 버전에 맞는 ChromeDriver 다운로드 시도
log_info "Chrome $CHROME_VERSION에 맞는 ChromeDriver 다운로드 시도 중..."

# Chrome 139 버전에 맞는 ChromeDriver 다운로드 시도
log_info "Chrome 139용 ChromeDriver 다운로드 시도 중..."

# 방법 1: Chrome for Testing에서 139 버전 시도
if wget -q "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/139.0.7258.138/linux64/chromedriver-linux64.zip" -O chromedriver.zip; then
    log_info "Chrome for Testing에서 ChromeDriver 139 다운로드 성공"
    unzip -q chromedriver.zip
    sudo mv chromedriver-linux64/chromedriver /usr/local/bin/
    sudo chmod +x /usr/local/bin/chromedriver
    rm -rf chromedriver.zip chromedriver-linux64/
    log_info "ChromeDriver 139 설치 완료"
else
    log_warning "Chrome for Testing에서 139 버전 다운로드 실패. 138 버전 시도..."
    
    # 방법 2: Chrome 138 버전 시도
    if wget -q "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/138.0.7258.138/linux64/chromedriver-linux64.zip" -O chromedriver.zip; then
        log_info "Chrome for Testing에서 ChromeDriver 138 다운로드 성공"
        unzip -q chromedriver.zip
        sudo mv chromedriver-linux64/chromedriver /usr/local/bin/
        sudo chmod +x /usr/local/bin/chromedriver
        rm -rf chromedriver.zip chromedriver-linux64/
        log_info "ChromeDriver 138 설치 완료"
    else
        log_warning "Chrome for Testing에서 138 버전도 실패. 137 버전 시도..."
        
        # 방법 3: Chrome 137 버전 시도
        if wget -q "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/137.0.7258.138/linux64/chromedriver-linux64.zip" -O chromedriver.zip; then
            log_info "Chrome for Testing에서 ChromeDriver 137 다운로드 성공"
            unzip -q chromedriver.zip
            sudo mv chromedriver-linux64/chromedriver /usr/local/bin/
            sudo chmod +x /usr/local/bin/chromedriver
            rm -rf chromedriver.zip chromedriver-linux64/
            log_info "ChromeDriver 137 설치 완료"
        else
            log_error "모든 Chrome for Testing 버전 다운로드 실패. GitHub에서 최신 버전 시도..."
            
            # 방법 4: GitHub에서 최신 릴리즈
            CHROMEDRIVER_LATEST=$(curl -sS https://api.github.com/repos/google/chromedriver/releases/latest | grep -o '"tag_name": "v[^"]*"' | cut -d'"' -f4)
            if [[ -n "$CHROMEDRIVER_LATEST" ]]; then
                log_info "GitHub에서 ChromeDriver $CHROMEDRIVER_LATEST 다운로드 중..."
                wget "https://github.com/google/chromedriver/releases/download/${CHROMEDRIVER_LATEST}/chromedriver_linux64.zip"
                unzip chromedriver_linux64.zip
                sudo mv chromedriver /usr/local/bin/
                sudo chmod +x /usr/local/bin/chromedriver
                rm chromedriver_linux64.zip
                log_info "GitHub에서 ChromeDriver 설치 완료"
            else
                log_error "모든 방법으로 ChromeDriver 다운로드에 실패했습니다."
                exit 1
            fi
        fi
    fi
fi

# Chrome 및 ChromeDriver 버전 확인
log_info "Chrome 버전 확인:"
google-chrome --version
log_info "ChromeDriver 버전 확인:"
chromedriver --version

# ChromeDriver 호환성 테스트
log_info "ChromeDriver 호환성 테스트 중..."
if timeout 10s chromedriver --version >/dev/null 2>&1; then
    log_info "✅ ChromeDriver 테스트 성공"
else
    log_warning "⚠️ ChromeDriver 테스트 중 일부 문제 발생"
fi

# 프로젝트 디렉토리 생성
log_step "프로젝트 디렉토리 설정"
PROJECT_DIR="/opt/kbo_crawler"
log_info "프로젝트 디렉토리: $PROJECT_DIR"

sudo mkdir -p $PROJECT_DIR
sudo chown $USER:$USER $PROJECT_DIR

# 프로젝트 파일 복사 (고정 경로 사용)
SRC_DIR="/home/test/new"
log_info "프로젝트 소스 경로: $SRC_DIR"

if [[ -d "$SRC_DIR" && -f "$SRC_DIR/manage.py" ]]; then
    log_info "프로젝트 파일 복사 중..."
    cp -r "$SRC_DIR"/* $PROJECT_DIR/
    log_info "프로젝트 파일 복사 완료"
else
    log_error "프로젝트 경로를 찾을 수 없습니다: $SRC_DIR"
    log_error "manage.py 파일이 존재하는지 확인하세요."
    exit 1
fi

# Python 가상환경 생성
log_step "Python 가상환경 설정"
cd $PROJECT_DIR
log_info "가상환경 생성 중..."
python3.13 -m venv venv
source venv/bin/activate

log_info "pip 업그레이드 중..."
pip install --upgrade pip setuptools wheel

# requirements.txt 설치
log_step "Python 패키지 설치"
log_info "requirements.txt 설치 중..."
pip install -r requirements.txt
log_info "Python 패키지 설치 완료"

# 환경변수 파일 생성
log_step "환경변수 파일 생성"
log_info ".env 파일 생성 중..."

cat > $PROJECT_DIR/.env << EOF
# MySQL 데이터베이스 설정 (서버 2 연결)
DB_NAME=kbo_db
DB_USER=kbo_user
DB_PASSWORD=test
DB_HOST=$MYSQL_SERVER_IP
DB_PORT=3306

# Django 설정
SECRET_KEY=dev-secret-key-change-me-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,$(hostname -I | awk '{print $1}')

# 온프레미스 설정
STORAGE_TYPE=local
MEDIA_ROOT=./media
STATIC_ROOT=./staticfiles
EOF

log_info ".env 파일 생성 완료"

# 방화벽 설정 (MySQL 연결 테스트 전에 먼저 설정)
log_step "방화벽 설정"
log_info "방화벽 설정 중..."
echo "y" | sudo ufw enable
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw status

# MySQL 연결 테스트
log_step "MySQL 연결 테스트"
log_info "서버 2 MySQL 연결 테스트 중..."

# MySQL 클라이언트 설치
sudo apt install -y mysql-client

# 연결 테스트 (3번 시도)
log_info "MySQL 연결 테스트 중... (최대 3번 시도)"
MAX_RETRIES=3
RETRY_COUNT=0

while [[ $RETRY_COUNT -lt $MAX_RETRIES ]]; do
    if mysql -h $MYSQL_SERVER_IP -u kbo_user -ptest -e "SELECT 'Connection successful' as status;" 2>/dev/null; then
        log_info "MySQL 연결 테스트 성공!"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [[ $RETRY_COUNT -lt $MAX_RETRIES ]]; then
            log_warning "MySQL 연결 테스트 실패! ($RETRY_COUNT/$MAX_RETRIES) 5초 후 재시도..."
            sleep 5
        else
            log_error "MySQL 연결 테스트 최종 실패!"
            log_warning "서버 2의 MySQL이 실행 중이고 방화벽이 설정되었는지 확인하세요."
            log_warning "계속 진행하려면 Enter를 누르세요 (수동으로 나중에 연결 설정 가능)..."
            read -p ""
        fi
    fi
done

# Django 마이그레이션
log_step "Django 데이터베이스 마이그레이션"
log_info "Django 마이그레이션 실행 중..."
cd $PROJECT_DIR
source venv/bin/activate

# 기존 마이그레이션 파일 정리 (필요시)
log_info "기존 마이그레이션 파일 정리 중..."
rm -rf kbo/migrations/0*.py

# 새로운 마이그레이션 생성 및 적용
log_info "새로운 마이그레이션 생성 중..."
python manage.py makemigrations
log_info "마이그레이션 적용 중..."
python manage.py migrate
log_info "Django 마이그레이션 완료"

# Django 최소 설정 확인
log_step "Django 최소 설정 확인"
log_info "Django가 최소 설정으로 구성되었습니다."
log_info "인증, 세션, 관리자 기능이 비활성화되어 있습니다."

# 정적 파일 수집
log_step "정적 파일 수집"
log_info "정적 파일 수집 중..."
python manage.py collectstatic --noinput
log_info "정적 파일 수집 완료"

# 로그 디렉토리 생성
log_step "로그 디렉토리 생성"
mkdir -p $PROJECT_DIR/logs
log_info "로그 디렉토리 생성 완료"

# 개발 서버 실행 안내
log_step "개발 서버 실행 안내"
log_info "개발 서버를 실행하려면 다음 명령어를 사용하세요:"
log_info "cd $PROJECT_DIR && source venv/bin/activate"
log_info "python manage.py runserver 0.0.0.0:8001"
log_info ""
log_info "프로덕션 서버 설정은 별도로 구성하세요."

# 크롤링 스크립트 생성
log_step "크롤링 스크립트 생성"
log_info "크롤링 스크립트 생성 중..."

cat > $PROJECT_DIR/crawl_all_kbo.sh << 'EOF'
#!/bin/bash
cd /opt/kbo_crawler
source venv/bin/activate

# KBO 데이터 크롤링
python manage.py fetch_kbo2 --verbosity 2

echo "$(date): KBO 크롤링 완료" >> /opt/kbo_crawler/logs/crawl.log
EOF

chmod +x $PROJECT_DIR/crawl_all_kbo.sh
log_info "크롤링 스크립트 생성 완료"
log_info "수동 크롤링: ./crawl_all_kbo.sh"

# 방화벽 상태 확인 (이미 설정됨)
log_info "방화벽 상태 확인:"
sudo ufw status

# 최종 확인
log_step "설치 완료 확인"
log_info "설치 상태 확인 중..."

log_info "방화벽 상태:"
sudo ufw status

echo ""
log_info "=================================="
log_info "서버 1 Django + 크롤링 설치 완료!"
log_info "=================================="
log_info "프로젝트 디렉토리: $PROJECT_DIR"
log_info "Django 관리자: 비활성화됨 (최소 설정)"
log_info "사용자 계정: 불필요"
log_info "크롤링: 수동 실행 (./crawl_all_kbo.sh)"
log_info "로그 위치: $PROJECT_DIR/logs/"
echo ""
log_warning "서버 2 MySQL 연결: $MYSQL_SERVER_IP:3306"
echo ""
log_info "개발 서버 실행:"
log_info "cd $PROJECT_DIR && source venv/bin/activate"
log_info "python manage.py runserver 0.0.0.0:8001"
echo ""
log_info "크롤링 실행:"
log_info "./crawl_all_kbo.sh"
