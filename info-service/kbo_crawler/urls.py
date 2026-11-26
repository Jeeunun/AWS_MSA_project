from django.urls import path, include
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.db import connection
from django.db.utils import OperationalError
import json
import os
from datetime import datetime
from kbo import api_views

def health_check(request):
    """서버 상태 확인용 헬스 체크 엔드포인트"""
    return HttpResponse("OK", status=200)

def detailed_health_check(request):
    """상세한 서버 상태 확인용 헬스 체크 엔드포인트"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "server": "KBO Info Django Server",
        "version": "1.0.0"
    }

    # 데이터베이스 연결 상태 확인
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status["database"] = "connected"
            health_status["database_status"] = "OK"
    except OperationalError:
        health_status["database"] = "disconnected"
        health_status["database_status"] = "ERROR"
        health_status["status"] = "unhealthy"

    # 환경 변수 확인
    health_status["environment"] = {
        "debug": os.environ.get('DEBUG', 'False'),
        "allowed_hosts": os.environ.get('ALLOWED_HOSTS', '*'),
        "aws_region": os.environ.get('AWS_DEFAULT_REGION', 'ap-northeast-2')
    }

    # 상태 코드 결정
    status_code = 200 if health_status["status"] == "healthy" else 503

    return JsonResponse(health_status, status=status_code)

def url_debug(request):
    """URL 디버깅용 엔드포인트"""
    print(f"=== URL 디버깅 ===")
    print(f"요청 경로: {request.path}")
    print(f"요청 메서드: {request.method}")
    print(f"요청 헤더: {dict(request.headers)}")
    return JsonResponse({
        'message': 'URL 디버깅 엔드포인트',
        'path': request.path,
        'method': request.method
    })

urlpatterns = [
    # API Gateway /prod stage 지원
    path('prod/api/info/', include('kbo.urls')),  # /prod/api/info/* → API (API Gateway용)
    path('api/info/', include('kbo.urls')),       # /api/info/* → API (기존)
    path('info/', include('kbo.urls')),           # /info/* → API (프론트엔드용)

    # 헬스체크 및 디버깅
    path('health/', health_check, name='health_check'),
    path('health/detailed/', detailed_health_check, name='detailed_health_check'),
    path('debug/', url_debug, name='url_debug'),

    # 루트 레벨 API (마지막에 배치)
    path('', include('kbo.urls')),                # /* → API (루트 레벨)
]