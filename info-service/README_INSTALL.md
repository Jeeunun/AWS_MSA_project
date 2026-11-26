# KBO 크롤러 설치 가이드 (Ubuntu 24.04)

## 🏗️ **아키텍처 개요**

이 프로젝트는 Ubuntu 24.04에서 2개의 서버로 나누어 구성됩니다:

- **서버 1**: Django 웹 서버 + 크롤링 서버 (Firefox 사용)
- **서버 2**: MySQL 데이터베이스 전용 서버

## 📋 **시스템 요구사항**

### 서버 1 (Django + 크롤링)
- Ubuntu 24.04 LTS
- 최소 2GB RAM
- 최소 20GB 디스크 공간
- Python 3.13
- Firefox ESR + GeckoDriver

### 서버 2 (MySQL)
- Ubuntu 24.04 LTS
- 최소 1GB RAM
- 최소 10GB 디스크 공간
- MySQL 8.0

## 🚀 **설치 순서**

### 1단계: 서버 2 (MySQL) 설치

```bash
# 서버 2에서 실행
chmod +x install_mysql_server2.sh
./install_mysql_server2.sh
```

**설치 완료 후 확인사항:**
- MySQL 서비스 상태: `sudo systemctl status mysql`
- 방화벽 상태: `sudo ufw status`
- MySQL 서버 IP 주소 기록 (서버 1에서 필요)

### 2단계: 서버 1 (Django + 크롤링) 설치

```bash
# 서버 1에서 실행
chmod +x install_django_server1.sh
./install_django_server1.sh
```

**설치 과정에서 필요한 정보:**
- 서버 2의 MySQL IP 주소 입력
- Django 관리자 계정 생성

### 3단계: 환경변수 설정 및 테스트

```bash
# 환경변수 설정
export DB_HOST=192.168.111.134
export DB_USER=kbo_user
export DB_PASSWORD=test
export DB_NAME=kbo_db

# 데이터베이스 연결 테스트
python manage.py check --database default

# 크롤링 테스트 (LG 팀만)
python manage.py fetch_kbo2 --only LG
```

**또는 테스트 스크립트 사용:**
```bash
chmod +x test_db_connection.sh
./test_db_connection.sh
```

## 🔧 **주요 기능**

### 크롤링 기능
- **fetch_kbo2.py**: KBO 선수 및 팀 정보 크롤링
- **crawl_player_images.py**: 선수 이미지 크롤링
- **upload_player_images.py**: 이미지 업로드

### 자동화
- 매일 새벽 2시 자동 크롤링
- Supervisor를 통한 프로세스 관리
- Nginx를 통한 웹 서버 제공

## 🌐 **접속 정보**

### 웹 인터페이스
- **메인 사이트**: `http://[서버1_IP]`
- **관리자 페이지**: `http://[서버1_IP]/admin`

### 데이터베이스
- **호스트**: `[서버2_IP]`
- **포트**: 3306
- **데이터베이스**: `kbo_db`
- **사용자**: `kbo_user`
- **비밀번호**: `test`

## 📁 **프로젝트 구조**

```
/opt/kbo_crawler/
├── venv/                    # Python 가상환경
├── kbo_crawler/            # Django 프로젝트 설정
├── kbo/                    # Django 앱
├── manage.py               # Django 관리 명령어
├── requirements.txt        # Python 패키지 목록
├── .env                    # 환경변수 설정
├── gunicorn.conf.py       # Gunicorn 설정
├── crawl_kbo.sh           # 크롤링 자동화 스크립트
└── logs/                  # 로그 파일들
```

## 🛠️ **수동 명령어**

### 크롤링 실행
```bash
cd /opt/kbo_crawler
source venv/bin/activate

# 선수 데이터 크롤링
python manage.py fetch_kbo2

# 선수 이미지 크롤링
python manage.py crawl_player_images

# 이미지 업로드
python manage.py upload_player_images
```

### 서비스 관리
```bash
# Django 서비스 상태 확인
sudo supervisorctl status kbo_crawler

# Django 서비스 재시작
sudo supervisorctl restart kbo_crawler

# Nginx 상태 확인
sudo systemctl status nginx

# MySQL 상태 확인 (서버 2에서)
sudo systemctl status mysql
```

## 🔍 **문제 해결**

### 일반적인 문제들

#### 1. MySQL 연결 실패
```bash
# 서버 2에서 MySQL 상태 확인
sudo systemctl status mysql

# 방화벽 확인
sudo ufw status

# MySQL 원격 접속 설정 확인
sudo grep "bind-address" /etc/mysql/mysql.conf.d/mysqld.cnf
```

#### 2. Firefox/GeckoDriver 문제
```bash
# Firefox 버전 확인
firefox --version

# GeckoDriver 버전 확인
geckodriver --version

# Ubuntu 24.04에서 Firefox 패키지 문제가 있는 경우
# 1. 기본 firefox 패키지 설치 시도
sudo apt install firefox

# 2. Mozilla 공식 저장소 추가
sudo add-apt-repository ppa:mozillateam/ppa -y
sudo apt update
sudo apt install firefox

# 3. 수동으로 GeckoDriver 재설치
cd /tmp
wget https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux64.tar.gz
tar -xzf geckodriver-v0.33.0-linux64.tar.gz
sudo mv geckodriver /usr/local/bin/
sudo chmod +x /usr/local/bin/geckodriver
```

#### 3. Django 마이그레이션 오류
```bash
cd /opt/kbo_crawler
source venv/bin/activate

# 마이그레이션 상태 확인
python manage.py showmigrations

# 마이그레이션 강제 실행
python manage.py migrate --run-syncdb
```

## 📊 **모니터링**

### 로그 파일 위치
- **Django 로그**: `/opt/kbo_crawler/logs/`
- **Nginx 로그**: `/var/log/nginx/`
- **MySQL 로그**: `/var/log/mysql/`
- **크롤링 로그**: `/opt/kbo_crawler/logs/crawl.log`

### 시스템 모니터링
```bash
# 시스템 리소스 확인
htop
df -h
free -h

# 서비스 상태 확인
sudo systemctl status nginx mysql supervisor
sudo supervisorctl status
```

## 🔒 **보안 고려사항**

### 방화벽 설정
- SSH (22번 포트): 서버 1, 2 모두
- HTTP (80번 포트): 서버 1만
- MySQL (3306번 포트): 서버 2만

### 데이터베이스 보안
- 기본 비밀번호 변경 권장
- 특정 IP에서만 접근 허용 설정 가능
- SSL/TLS 연결 설정 가능

## 📞 **지원**

문제가 발생하면 다음을 확인하세요:
1. 로그 파일 확인
2. 서비스 상태 확인
3. 네트워크 연결 확인
4. 방화벽 설정 확인

## 📝 **변경 이력**

- **2024-08-24**: Ubuntu 24.04 지원, Firefox 사용으로 변경
- **2024-08-24**: 2개 서버 분리 구성 지원
- **2024-08-24**: 자동화 스크립트 추가
