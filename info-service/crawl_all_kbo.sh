#!/bin/bash

# KBO 통합 크롤링 스크립트
# 모든 KBO 데이터를 한번에 수집합니다.

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

# 프로젝트 디렉토리 확인
PROJECT_DIR="/opt/kbo_crawler"
if [[ ! -d "$PROJECT_DIR" ]]; then
    log_error "프로젝트 디렉토리를 찾을 수 없습니다: $PROJECT_DIR"
    log_info "현재 디렉토리에서 실행하려면 Enter를 누르세요..."
    read -p ""
    PROJECT_DIR="$(pwd)"
fi

log_info "프로젝트 디렉토리: $PROJECT_DIR"

# 가상환경 활성화
log_step "가상환경 활성화"
cd "$PROJECT_DIR"

if [[ ! -d "venv" ]]; then
    log_error "가상환경을 찾을 수 없습니다!"
    exit 1
fi

log_info "가상환경 활성화 중..."
source venv/bin/activate
log_info "가상환경 활성화 완료"

# Python 버전 확인
log_info "Python 버전:"
python --version

# Django 상태 확인
log_step "Django 상태 확인"
log_info "Django 상태 확인 중..."
if ! python manage.py check >/dev/null 2>&1; then
    log_error "Django 설정에 문제가 있습니다!"
    exit 1
fi
log_info "Django 상태 정상"

# 데이터베이스 연결 확인
log_step "데이터베이스 연결 확인"
log_info "데이터베이스 연결 테스트 중..."
if ! python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT 1'); print('데이터베이스 연결 성공')" >/dev/null 2>&1; then
    log_error "데이터베이스 연결에 실패했습니다!"
    exit 1
fi
log_info "데이터베이스 연결 성공"

# 크롤링 시작
log_step "KBO 데이터 크롤링 시작"
log_info "크롤링을 시작합니다..."

# 1. 팀 및 선수 기본 정보 크롤링
log_info "1단계: 팀 및 선수 기본 정보 크롤링 중..."
if python manage.py fetch_kbo2 --verbosity 2; then
    log_info "✅ 팀 및 선수 기본 정보 크롤링 완료"
else
    log_error "❌ 팀 및 선수 기본 정보 크롤링 실패"
    log_warning "계속 진행하려면 Enter를 누르세요..."
    read -p ""
fi

# 2. 선수 이미지 크롤링 (선택사항)
log_info "2단계: 선수 이미지 크롤링 중..."
read -p "선수 이미지도 크롤링하시겠습니까? (y/n): " CRAWL_IMAGES

if [[ "$CRAWL_IMAGES" =~ ^[Yy]$ ]]; then
    log_info "선수 이미지 크롤링 시작..."
    if python manage.py crawl_player_images --verbosity 2; then
        log_info "✅ 선수 이미지 크롤링 완료"
    else
        log_warning "⚠️ 선수 이미지 크롤링 중 일부 오류 발생"
    fi
else
    log_info "선수 이미지 크롤링을 건너뜁니다."
fi

# 3. 이미지 업로드 (선택사항)
if [[ "$CRAWL_IMAGES" =~ ^[Yy]$ ]]; then
    log_info "3단계: 이미지 업로드 중..."
    read -p "크롤링한 이미지를 업로드하시겠습니까? (y/n): " UPLOAD_IMAGES
    
    if [[ "$UPLOAD_IMAGES" =~ ^[Yy]$ ]]; then
        log_info "이미지 업로드 시작..."
        if python manage.py upload_player_images --verbosity 2; then
            log_info "✅ 이미지 업로드 완료"
        else
            log_warning "⚠️ 이미지 업로드 중 일부 오류 발생"
        fi
    else
        log_info "이미지 업로드를 건너뜁니다."
    fi
fi

# 4. 데이터베이스 통계 확인
log_step "크롤링 결과 확인"
log_info "데이터베이스 통계 확인 중..."

python manage.py shell -c "
from kbo.models import Team, Player, Manager
from django.db.models import Count

print('=== KBO 데이터베이스 통계 ===')
print(f'팀 수: {Team.objects.count()}')
print(f'선수 수: {Player.objects.count()}')
print(f'감독 수: {Manager.objects.count()}')

if Team.objects.count() > 0:
    print('\n=== 팀별 선수 수 ===')
    teams = Team.objects.annotate(player_count=Count('player'))
    for team in teams:
        print(f'{team.name}: {team.player_count}명')

if Player.objects.count() > 0:
    print('\n=== 포지션별 선수 수 ===')
    positions = Player.objects.values('position').annotate(count=Count('id')).order_by('-count')
    for pos in positions:
        print(f'{pos[\"position\"]}: {pos[\"count\"]}명')
"

# 5. 정적 파일 수집
log_step "정적 파일 정리"
log_info "정적 파일 수집 중..."
python manage.py collectstatic --noinput
log_info "정적 파일 수집 완료"

# 완료 메시지
log_step "크롤링 완료"
log_info "🎉 KBO 데이터 크롤링이 완료되었습니다!"
log_info "웹 브라우저에서 다음 URL로 확인하세요:"
log_info "메인 페이지: http://$(hostname -I | awk '{print $1}'):8001/players/"
log_info "관리자 페이지: 비활성화됨 (최소 설정)"

echo ""
log_info "수동 크롤링 명령어:"
log_info "cd $PROJECT_DIR && source venv/bin/activate"
log_info "python manage.py fetch_kbo2 --only <팀코드>  # 특정 팀만"
log_info "python manage.py fetch_kbo2 --no-browser     # 브라우저 없이"
echo ""

# 로그 파일에 기록
LOG_FILE="$PROJECT_DIR/logs/crawl_$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$(dirname "$LOG_FILE")"
echo "$(date): KBO 통합 크롤링 완료" >> "$LOG_FILE"
log_info "로그 파일: $LOG_FILE"
