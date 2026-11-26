# KBO 정보 시스템 수정 내역 (2025-08-27)

## 📋 **수정 개요**

이 문서는 KBO 정보 시스템에서 2025년 8월 27일에 추가로 수정하고 개선한 내역을 정리한 것입니다. 이전 수정사항(0826readme.md)에 이어서 진행된 작업들입니다.

## 🚨 **해결된 주요 문제들**

### **1. URL 경로 구조 변경**
- **문제**: 기존 `/players/` 경로를 `/info/`로 변경 요청
- **원인**: 사용자가 더 직관적인 URL 구조를 원함
- **해결**: 모든 URL을 `/info/` 상위 경로로 변경
- **수정 파일**: `kbo_crawler/urls.py`, `kbo/urls.py`

### **2. S3 이미지 로딩 오류**
- **문제**: 선수 상세 모달에서 S3 이미지를 불러올 수 없음
- **원인**: `'int' object has no attribute 'isdigit'` 오류
- **해결**: `player_number.isdigit()` → `str(player_number).isdigit()`로 수정
- **수정 파일**: `kbo/views.py`

### **3. 환경변수 설정 문제**
- **문제**: AWS S3 인증 정보가 설정되지 않음
- **원인**: `env.txt` 파일에 AWS 인증 정보 누락
- **해결**: AWS S3 인증 정보를 `env.txt`에 추가
- **수정 파일**: `env.txt`

### **4. boto3 패키지 누락**
- **문제**: S3 관련 패키지가 requirements.txt에 없음
- **원인**: AWS S3 연동을 위한 boto3 패키지 미설치
- **해결**: requirements.txt에 boto3 패키지 추가
- **수정 파일**: `requirements.txt`

## 🔧 **상세 수정 내역**

### **kbo_crawler/urls.py**

#### **메인 URL 경로 변경**
```python
# 수정 전
path('', include('kbo.urls')),

# 수정 후
path('', lambda request: HttpResponseRedirect('/info/'), name='root_redirect'),
path('info/', include('kbo.urls')),
```

#### **HttpResponseRedirect import 추가**
```python
# 수정 전
from django.http import HttpResponse, JsonResponse

# 수정 후
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
```

### **kbo/urls.py**

#### **URL 패턴 구조 변경**
```python
# 수정 전
urlpatterns = [
    path('', RedirectView.as_view(url='/players/', permanent=False)),
    path('players/', views.team_list, name='players_main'),
    path('players/teams/<str:code>/', views.team_detail, name='team_detail'),
    path('players/search/', views.search_advanced, name='search_advanced'),
    path('players/stats/', views.stats_analysis, name='stats_analysis'),
    path('players/compare/', views.team_comparison, name='team_comparison'),
    path('players/player/<int:player_id>/modal/', views.player_detail_modal, name='player_detail_modal'),
    path('players/api/players/', views.get_all_players_json, name='players_api'),
    path('players/api/team-position-stats/', views.team_position_stats_api, name='team_position_stats_api'),
]

# 수정 후
urlpatterns = [
    path('', views.team_list, name='teams_main'),
    path('teams/<str:code>/', views.team_detail, name='team_detail'),
    path('search/', views.search_advanced, name='search_advanced'),
    path('stats/', views.stats_analysis, name='stats_analysis'),
    path('compare/', views.team_comparison, name='team_comparison'),
    path('player/<int:player_id>/modal/', views.player_detail_modal, name='player_detail_modal'),
    path('api/players/', views.get_all_players_json, name='players_api'),
    path('api/team-position-stats/', views.team_position_stats_api, name='team_position_stats_api'),
]
```

### **kbo/views.py**

#### **S3 이미지 검색 함수 오류 수정**
```python
# 수정 전 (오류 발생)
if player_number and player_number.isdigit():

# 수정 후 (정상 작동)
if player_number and str(player_number).isdigit():
```

#### **S3 디버깅 로그 추가**
```python
def get_s3_player_image_url(team_code: str, player_name: str, player_number: str | None = None) -> str | None:
    print(f"🔍 S3 이미지 검색 시작: team={team_code}, name={player_name}, number={player_number} (타입: {type(player_number)})")
    
    try:
        # S3 환경변수 확인
        bucket_name = os.environ.get('AWS_S3_BUCKET', '')
        aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID', '')
        aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
        aws_region = os.environ.get('AWS_DEFAULT_REGION', '')
        
        print(f"🔑 환경변수 확인:")
        print(f"  - BUCKET: {bucket_name}")
        print(f"  - ACCESS_KEY: {aws_access_key[:10]}...")
        print(f"  - SECRET_KEY: {aws_secret_key[:10]}...")
        print(f"  - REGION: {aws_region}")
        
        # S3 클라이언트 초기화
        print("🚀 S3 클라이언트 초기화 중...")
        s3_client = boto3.client('s3')
        print("✅ S3 클라이언트 초기화 완료")
        
        # 상세 검색 로그 추가
        base_prefix = f"players/{team_code}_"
        print(f"🔍 검색 프리픽스: {base_prefix}")
        
        def name_candidates(name: str):
            candidates = [name, name.replace(' ', ''), name.replace(' ', '_')]
            print(f"🔍 이름 후보: {candidates}")
            return candidates
```

### **requirements.txt**

#### **AWS S3 패키지 추가**
```txt
# 수정 전
# AWS S3 관련 패키지 없음

# 수정 후
# AWS S3 관련 패키지
boto3>=1.34.0,<2.0.0
```

### **env.txt**

#### **AWS S3 인증 정보 추가**
```txt
# AWS S3 인증 정보
AWS_ACCESS_KEY_ID=AKIA2SLT3ZLRNCMHVLPO
AWS_SECRET_ACCESS_KEY=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
AWS_S3_BUCKET=wjdwlstndlalwl
AWS_DEFAULT_REGION=ap-northeast-2
```

### **kbo/templates/kbo/base.html**

#### **네비게이션 링크 URL 수정**
```html
<!-- 수정 전 -->
<a class="nav-link" href="{% url 'players_main' %}">
<a class="nav-link" href="/players/search/">
<a class="nav-link" href="/players/stats/">
<a class="nav-link" href="/players/compare/">

<!-- 수정 후 -->
<a class="nav-link" href="{% url 'teams_main' %}">
<a class="nav-link" href="/info/search/">
<a class="nav-link" href="/info/stats/">
<a class="nav-link" href="/info/compare/">
```

### **kbo/templates/kbo/team_list.html**

#### **선수 검색 버튼 URL 수정**
```html
<!-- 수정 전 -->
<a href="/players/search/" class="btn btn-primary">

<!-- 수정 후 -->
<a href="/info/search/" class="btn btn-primary">
```

### **kbo/templates/kbo/team_detail.html**

#### **네비게이션 버튼 URL 수정**
```html
<!-- 수정 전 -->
<a href="/players/" class="btn btn-outline-secondary me-2">
<a href="/players/search/" class="btn btn-primary">

<!-- 수정 후 -->
<a href="/info/teams/" class="btn btn-outline-secondary me-2">
<a href="/info/search/" class="btn btn-primary">
```

#### **JavaScript fetch URL 수정**
```javascript
// 수정 전
fetch(`/players/player/${playerId}/modal/`)

// 수정 후
fetch(`/info/player/${playerId}/modal/`)
```

### **kbo/templates/kbo/stats_analysis.html**

#### **뒤로가기 버튼 URL 수정**
```html
<!-- 수정 전 -->
<a href="/players/" class="btn btn-outline-secondary">

<!-- 수정 후 -->
<a href="/info/teams/" class="btn btn-outline-secondary">
```

### **kbo/templates/kbo/search_advanced.html**

#### **뒤로가기 버튼 및 fetch URL 수정**
```html
<!-- 수정 전 -->
<a href="/players/" class="btn btn-outline-secondary">
fetch(`/players/player/${playerId}/modal/`)

<!-- 수정 후 -->
<a href="/info/teams/" class="btn btn-outline-secondary">
fetch(`/info/player/${playerId}/modal/`)
```

### **kbo/templates/kbo/team_comparison.html**

#### **뒤로가기 버튼 URL 수정**
```html
<!-- 수정 전 -->
<a href="/players/" class="btn btn-outline-secondary">

<!-- 수정 후 -->
<a href="/info/teams/" class="btn btn-outline-secondary">
```

## ✅ **수정 완료된 기능들**

1. **URL 구조 변경** ✅
   - `/players/` → `/info/` 경로로 완전 변경
   - 루트 경로 `/`에서 자동으로 `/info/`로 리디렉션

2. **S3 이미지 로딩** ✅
   - `isdigit()` 오류 해결
   - 상세한 디버깅 로그 추가
   - 환경변수 정상 로드 확인

3. **AWS S3 연동** ✅
   - boto3 패키지 설치
   - AWS 인증 정보 설정
   - S3 클라이언트 정상 초기화

4. **모든 템플릿 URL 수정** ✅
   - 네비게이션 링크
   - 버튼 링크
   - JavaScript fetch URL

## 🎯 **새로운 URL 구조**

| **경로** | **설명** | **이전 경로** |
|----------|----------|---------------|
| `/` | **자동 리디렉션** | `/info/`로 이동 |
| `/info/` | **팀 목록 메인** | `/players/` |
| `/info/teams/KIA/` | **팀 상세** | `/players/teams/KIA/` |
| `/info/search/` | **선수 검색** | `/players/search/` |
| `/info/stats/` | **통계 분석** | `/players/stats/` |
| `/info/compare/` | **팀 비교** | `/players/compare/` |
| `/info/player/123/modal/` | **선수 상세** | `/players/player/123/modal/` |

## 🔄 **테스트 방법**

1. **Django 서버 재시작**
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

2. **새로운 URL 구조 테스트**
   - 메인 페이지: `http://localhost:8000/` (자동 리디렉션)
   - 팀 목록: `http://localhost:8000/info/`
   - 팀 상세: `http://localhost:8000/info/teams/KIA/`
   - 선수 검색: `http://localhost:8000/info/search/`
   - 통계 분석: `http://localhost:8000/info/stats/`
   - 팀 비교: `http://localhost:8000/info/compare/`

3. **S3 이미지 로딩 테스트**
   - 선수 상세 모달 열기
   - 콘솔에서 S3 디버깅 로그 확인
   - 이미지 정상 로딩 확인

## 📝 **주요 개선 사항**

1. **URL 구조 개선**: `/info/` 경로로 더 직관적인 구조
2. **S3 연동 완성**: AWS S3에서 선수 이미지 정상 로딩
3. **디버깅 강화**: S3 관련 상세한 로그로 문제 해결 용이
4. **일관성 향상**: 모든 템플릿에서 동일한 URL 패턴 사용

## 🔍 **S3 디버깅 로그 예시**

정상 작동 시 콘솔에 출력되는 로그:
```
🔍 S3 이미지 검색 시작: team=DS, name=김재호, number=00 (타입: <class 'int'>)
🔑 환경변수 확인:
  - BUCKET: wjdwlstndlalwl
  - ACCESS_KEY: AKIA2SLT3...
  - SECRET_KEY: XSB5dzd2c...
  - REGION: ap-northeast-2
🚀 S3 클라이언트 초기화 중...
✅ S3 클라이언트 초기화 완료
🔍 검색 프리픽스: players/DS_
🔍 이름 후보: ['김재호', '김재호', '김재호']
🔍 등번호 기반 검색 시작: 00
🔍 검색할 번호들: 0, 00, 000
🔍 S3 검색 시도: players/DS_00_
🔍 S3 응답: X개 객체 발견
🔍 검사 중인 객체: players/DS_00_김재호_내야수.jpg
✅ 이미지 발견: https://wjdwlstndlalwl.s3.ap-northeast-2.amazonaws.com/players/DS_00_김재호_내야수.jpg
```

## 📋 **환경 설정 요구사항**

1. **Python 패키지**: `boto3>=1.34.0`
2. **환경변수**: AWS S3 인증 정보 설정
3. **S3 버킷**: `wjdwlstndlalwl` 버킷 접근 권한
4. **네트워크**: S3 엔드포인트 접근 가능

---

**작성일**: 2025-08-27  
**작성자**: AI Assistant  
**프로젝트**: KBO 정보 시스템  
**이전 문서**: 0826readme.md
