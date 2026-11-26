# ⚾️ 이벤트 서비스 — 야구 커뮤니티 플랫폼 (KBO 예측/순위/일정)

> 야구 커뮤니티 플랫폼 내 **이벤트 서비스** 모듈의 리포지토리용 README입니다.  
> 백엔드 **Django(Python)**, 프론트 **React**, 배포 **AWS ECR/ECS + GitHub Actions**, 정기 작업 **EventBridge**, 보안 설정 **Secrets Manager** 기반.

---

## 📌 서비스 개요

**이벤트 서비스**는 KBO 리그 경기 정보를 바탕으로 다음 기능을 제공합니다.

- **경기 일정/결과 조회**: 날짜별 경기 스케줄과 스코어 확인
- **팀 순위 확인**: **종합 / 수비 / 공격** 순위 대시보드
- **승부 예측 참여**: 가까운 날짜의 경기에서 **원정 vs 홈 승리팀 예측**
  - **1일 1회**(사용자 계정 기준) 참여 제한
- **쿠폰 지급**: 예측이 실제 경기 승리팀과 일치하면 **쿠폰 자동 발급**

프론트/백 분리 구조에서, React 앱은 CloudFront/S3로 배포되고, API는 API Gateway → ALB → ECS(Fargate) → Django로 전달됩니다. 인증은 **Cognito(Authorization Code + PKCE)** 로 처리하며, API 호출은 `Authorization: Bearer <access_token>` 헤더를 사용합니다.

---

## 🧩 아키텍처 개요

```
[사용자]
   │
   ├─▶ Route53 / CloudFront ─▶ React(정적 호스팅, S3)
   │
   └─▶ (로그인) Cognito Hosted UI ──▶ 콜백(React) ──▶ /oauth2/token 교환(PKCE)
                                   │
React (Bearer 토큰) ─▶ API Gateway(Authorizer)
                      └─▶ VPC Link ─▶ Internal ALB ─▶ ECS(Fargate, Django)
                                                 └─▶ RDS (MariaDB)

[정기 작업] EventBridge(스케줄) ─▶ ECS RunTask (크롤러/관리 커맨드)
```

- **경로 기반 라우팅 예시(ALB)**: `/event*` → `event-service` (컨테이너 포트 **8002**)  
- **권장 헬스체크 경로**: `/event/healthz`

---

## 🏗️ 기술 스택

- **Backend**: Django, Python
- **Frontend**: React (Vite)
- **Infra**: AWS ECR, ECS(Fargate), ALB, RDS(MariaDB), Secrets Manager, EventBridge, CloudWatch Logs
- **CI/CD**: GitHub Actions

---

## 📁 디렉터리 구조(예시)

```text
event-msa/
├─ event/                     # 앱(도메인) 레이어
│  ├─ management/commands/    # Django 커맨드(크롤러 등)
│  ├─ migrations/             # 마이그레이션
│  ├─ templates/events/       # (선택) 서버 템플릿
│  ├─ api_views.py            # API 전용 뷰
│  ├─ serializers.py          # DRF 직렬화기
│  ├─ cognito_auth.py         # JWT/클레임 처리
│  ├─ urls.py                 # 앱 URL
│  └─ models.py               # ORM 모델(결과/순위/예측/쿠폰 등)
├─ event_service/             # 프로젝트 레이어
│  ├─ settings.py
│  ├─ urls.py                 # 글로벌 URL (예: /event/* 라우팅)
│  └─ wsgi.py                 # Gunicorn 엔트리
├─ Dockerfile
├─ requirements.txt
├─ manage.py
└─ README.md
```

---

## 🔑 핵심 기능 상세

### 1) 경기 일정 / 결과
- 날짜별 경기 목록 및 스코어 조회
- 최근/과거 검색 지원

### 2) 팀 순위
- **종합 / 공격 / 수비** 3개 지표
- 시즌/일자 기준 최신 순위 반영

### 3) 예측 참여 (1일 1회 제한)
- 가까운 경기(현재일 기준) 중 하나를 선택하여 **원정/홈 승리팀** 예측
- 사용자(토큰/계정) 기준 **하루 1건**으로 제한

### 4) 쿠폰 지급
- 실제 경기 결과의 **승리팀**이 사용자 예측과 같으면 **쿠폰 발급**
- 쿠폰 상태: `미사용 / 사용 / 만료`(필터 조회 제공)

---

## 🔗 API 엔드포인트 (예시)

> 실제 스키마/경로는 구현에 따라 다를 수 있습니다.

- `GET /event/schedule?date=YYYY-MM-DD` — 특정 날짜의 경기 일정
- `GET /event/result?date=YYYY-MM-DD` — 특정 날짜의 경기 결과
- `GET /event/ranks?type=total|attack|defense` — 팀 순위
- `POST /event/predict` — 예측 제출(예: `{ match_id, pick: "AWAY"|"HOME" }`)
- `GET /event/coupons?status=unused|used|expired` — 쿠폰 목록

**인증:** 모든 보호 엔드포인트는 `Authorization: Bearer <access_token>` 필요  
**CORS:** API Gateway에서 `Access-Control-Allow-Origin: https://<앱도메인>` 화이트리스트

---

## ⚙️ 환경 변수(.env 예시)

```ini
# Django
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=false
ALLOWED_HOSTS=*
CORS_ALLOWED_ORIGINS=https://app.example.com

# Database
DB_HOST=your-rds-endpoint
DB_PORT=3306
DB_NAME=event_service
DB_USER=event_user
DB_PASSWORD=********

# Cognito (Frontend와 일치해야 함)
COGNITO_REGION=ap-northeast-2
COGNITO_DOMAIN=https://<your-domain>.auth.ap-northeast-2.amazoncognito.com
COGNITO_USER_POOL_ID=ap-northeast-2_xxxxx
COGNITO_CLIENT_ID=xxxxxxxxxxxx
COGNITO_REDIRECT_URI=https://app.example.com/auth/callback

# 기타
TZ=Asia/Seoul
```

> 운영에서는 **Secrets Manager**에 저장하고 ECS 태스크에 주입하세요.

---

## 🐳 도커 & 로컬 실행

```bash
# 이미지 빌드
docker build -t event-service:local .

# 컨테이너 실행
docker run --rm -p 8002:8002 --env-file .env event-service:local

# (또는) 로컬 개발 서버
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8002
```

- 컨테이너는 **8002 포트**로 리슨(Gunicorn 바인드).  
- ECS 태스크 정의의 `containerPort=8002`, ALB 타깃그룹/리스너 규칙(`/event*`)와 일치해야 합니다.

---

## 🚀 CI/CD (GitHub Actions → ECR/ECS)

- **Build**: `docker/build-push-action` (캐시 활용, `latest` & `sha7` 태그)
- **Push**: `main` 브랜치 push 시 ECR로 자동 푸시
- (옵션) **배포 연동**: `amazon-ecs-render-task-definition` + `amazon-ecs-deploy-task-definition`을 추가해 ECS 서비스 무중단 배포

태그 예시:
```
<account>.dkr.ecr.ap-northeast-2.amazonaws.com/plan-b/event-service:latest
<account>.dkr.ecr.ap-northeast-2.amazonaws.com/plan-b/event-service:<short-sha>
```

---

## ⏰ 정기 작업 (크롤링/동기화)

- **EventBridge** 스케줄 → **ECS RunTask** 로 크롤러/갱신 커맨드 실행
  - 예: 자정에 순위/일정/결과 갱신 커맨드 실행
- CloudWatch Logs로 작업 결과 확인

