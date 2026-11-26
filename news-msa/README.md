# 🧢 News Community — Serverless-ish News Platform on AWS

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.x-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![MariaDB](https://img.shields.io/badge/MariaDB-10.x-003545?logo=mariadb&logoColor=white)](https://mariadb.org/)
[![AWS](https://img.shields.io/badge/AWS-Fargate%20%7C%20ECS%20%7C%20ECR%20%7C%20RDS%20%7C%20ALB-FF9900?logo=amazon-aws&logoColor=white)](https://aws.amazon.com/)
[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-CI%2FCD-2088FF?logo=github-actions&logoColor=white)](https://github.com/features/actions)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
<!-- [![CI](https://github.com/<YOUR_ORG>/<YOUR_REPO>/actions/workflows/deploy.yml/badge.svg)](https://github.com/<YOUR_ORG>/<YOUR_REPO>/actions/workflows/deploy.yml) -->

야구 커뮤니티 유저에게 최신 뉴스/크롤링 정보를 제공하는 **Django + MariaDB** 기반 서비스입니다.  
**GitHub Actions** 로 컨테이너 이미지를 빌드/배포하고, **AWS ECS on Fargate** 에서 애플리케이션이 동작합니다.  
정기 크롤링은 **EventBridge** 스케줄로 1시간 주기로 실행됩니다.

> 본 문서는 운영 환경 기준(Region: `ap-northeast-2`)으로 작성되었습니다.

---

## 🗺️ 목차

- [아키텍처 개요](#-아키텍처-개요)
- [기술 스택](#-기술-스택)
- [디렉터리 구조](#-디렉터리-구조)
- [배포 파이프라인](#-배포-파이프라인)
- [런타임 구성](#-런타임-구성)
  - [Secrets Manager 키 설계](#secrets-manager-키-설계)
  - [ECS 태스크 정의 포인트](#ecs-태스크-정의-포인트)
  - [ALB/Target Group 설정](#albtarget-group-설정)
  - [VPC 엔드포인트](#vpc-엔드포인트)
- [크롤링 작업 (EventBridge → ECS RunTask)](#-크롤링-작업-eventbridge--ecs-runtask)
- [로컬 개발 & 테스트](#-로컬-개발--테스트)
- [모니터링 & 로깅](#-모니터링--로깅)
- [트러블슈팅](#-트러블슈팅)
- [라이선스](#-라이선스)

---

## 🏗️ 아키텍처 개요

> ALB → ECS(Fargate) → Django 컨테이너 → RDS(MariaDB)  
> ECR로부터 이미지 Pull, Secrets Manager로 DB 크리덴셜/설정 주입, CloudWatch Logs로 애플리케이션 로그 집계.  
> EventBridge가 1시간 주기로 **news-task-crawl** 태스크를 RunTask로 실행.

```
[Client] ──▶ [ALB] ──▶ [ECS Service on Fargate] ──▶ [Django App]
                                   │
                                   ├─(pull image)──▶ [ECR]
                                   ├─(get secret)─▶ [Secrets Manager]
                                   └─(logs)───────▶ [CloudWatch Logs]

[EventBridge Schedule] ──▶ (RunTask) ──▶ [ECS Task: crawl_news.py] ──▶ [RDS]
```

*아키텍처 다이어그램 이미지는 `docs/architecture.png` 등을 추가해 README에 직접 링크하세요.*

---

## 🧰 기술 스택

- **Backend**: Django, Python 3.11+  
- **DB**: MariaDB (Amazon RDS)
- **Infra**: AWS ECS on Fargate, ECR, ALB, CloudWatch Logs, Secrets Manager, EventBridge, VPC Endpoints
- **CI/CD**: GitHub Actions (`.github/workflows/deploy.yml`)

---

## 📁 디렉터리 구조

```
.
├─ .github/
│  └─ workflows/
│     └─ deploy.yml
├─ aws/
│  └─ news-task.json
├─ news/
│  ├─ management/
│  │  └─ commands/
│  │     └─ crawl_news.py
│  ├─ migrations/
│  ├─ templates/
│  │  └─ news/
│  │     └─ news_list.html
│  ├─ admin.py
│  ├─ apps.py
│  ├─ models.py
│  ├─ tests.py
│  ├─ urls.py
│  └─ views.py
├─ news_service/
│  ├─ __init__.py
│  ├─ asgi.py
│  ├─ settings.py
│  ├─ urls.py
│  └─ wsgi.py
├─ Dockerfile
├─ manage.py
└─ requirements.txt
```

---

## 🚀 배포 파이프라인

`deploy.yml` 은 다음 순서로 동작합니다.

1. **이미지 빌드 & ECR Push**  
   - 태그: `:sha`, `:branch`(main→`latest`) 두 가지를 푸시
2. **태스크 정의 렌더링/등록**  
   - `aws/news-task.json`을 기반으로 이미지 태그와 로그/시크릿 구성을 주입한 뒤 `RegisterTaskDefinition`
3. **DB 준비 (one-off RunTask)**  
   - 컨테이너 **명령만 오버라이드**하여 `CREATE DATABASE IF NOT EXISTS` 실행
4. **마이그레이션 (one-off RunTask)**  
   - 같은 태스크 정의로 `python /app/manage.py migrate --noinput` 실행
5. **ECS 서비스 보장**  
   - 서비스가 없으면 `create-service`(ALB TargetGroup, awsvpc, Fargate), 있으면 스킵
6. **서비스 업데이트/배포**  
   - 새 태스크 정의 리비전으로 `update-service --force-new-deployment`
7. **안정화 대기**  
   - `aws ecs wait services-stable`

> DB/마이그레이션은 **애플리케이션 이미지 그대로** 실행하되, **command override** 로만 제어합니다.  
> 컨테이너 진입점/코드 수정 없이 안전하게 일회성 작업을 수행합니다.

---

## ⚙️ 런타임 구성

### Secrets Manager 키 설계

시크릿 이름(예): `prod/news/mariadb`

| 키(key) | 예시 값 |
|---|---|
| `username` | `admin` |
| `password` | `***` |
| `host` | `news.xxxxx.ap-northeast-2.rds.amazonaws.com` |
| `port` | `3306` |
| `name` | `news` |
| `engine` | `mariadb` |

> ECS 태스크 정의에서는 다음처럼 **키 단위 참조**를 사용합니다.
>
> ```json
> "secrets": [
>   {"name":"DB_HOST",     "valueFrom":"arn:aws:secretsmanager:...:secret:prod/news/mariadb-XXXX:host::"},
>   {"name":"DB_NAME",     "valueFrom":"arn:aws:secretsmanager:...:secret:prod/news/mariadb-XXXX:name::"},
>   {"name":"DB_USER",     "valueFrom":"arn:aws:secretsmanager:...:secret:prod/news/mariadb-XXXX:username::"},
>   {"name":"DB_PASSWORD", "valueFrom":"arn:aws:secretsmanager:...:secret:prod/news/mariadb-XXXX:password::"},
>   {"name":"DB_PORT",     "valueFrom":"arn:aws:secretsmanager:...:secret:prod/news/mariadb-XXXX:port::"}
> ]
> ```

**IAM 권한(Execution Role)** — 태스크가 Secrets를 읽으려면 *ecsTaskExecutionRole* 에 최소 다음 정책이 필요합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowReadDbSecret",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:ap-northeast-2:<ACCOUNT_ID>:secret:prod/news/mariadb-*"
    }
  ]
}
```

### ECS 태스크 정의 포인트

- **네트워킹**: `awsvpc`, 프라이빗 서브넷 + 보안그룹, `assignPublicIp=DISABLED`
- **로그**: `awslogs` 드라이버 (`/ecs/<service-name>`)
- **포트**: 컨테이너 `8000` (Django) → TargetGroup `HTTP:8000`
- **헬스체크**: `/healthz` 또는 `/` (서비스 라우팅에 맞게 수정)

### ALB/Target Group 설정

- Target Group **타입: `ip`** (Fargate 필수)
- 헬스체크 경로/응답코드 확인 (기본 `/` 200 OK)
- 리스너: `HTTP:80` (필요시 `HTTPS:443` 추가)

### VPC 엔드포인트

다음 엔드포인트를 **프라이빗 서브넷**에서 사용하면 인터넷 없이도 안전하게 통신할 수 있습니다.

- `com.amazonaws.ap-northeast-2.ecr.api`
- `com.amazonaws.ap-northeast-2.ecr.dkr`
- `com.amazonaws.ap-northeast-2.logs`
- `com.amazonaws.ap-northeast-2.secretsmanager`
- (이미지/정적 파일이 S3라면) `com.amazonaws.ap-northeast-2.s3`

---

## ⏱️ 크롤링 작업 (EventBridge → ECS RunTask)

- **룰 이름**: `news-crawling`
- **스케줄**: `rate(1 hour)`
- **타깃**: ECS `RunTask` (클러스터: `NEWS-CLUSTER`, 태스크 정의: `news-task-crawl`)
- **컨테이너 커맨드**: `python manage.py crawl_news` (Django management command)

> 크롤링 태스크에도 **ExecutionRole** 의 Secrets 권한이 필요합니다.

---

## 🧑‍💻 로컬 개발 & 테스트

```bash
# 1) 가상환경 & 의존성
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2) 로컬 DB(.env) — 예: docker로 마리아DB 띄우기
docker run -d --name mariadb \
  -e MARIADB_ROOT_PASSWORD=pass \
  -e MARIADB_DATABASE=news \
  -e MARIADB_USER=admin \
  -e MARIADB_PASSWORD=pass \
  -p 3306:3306 mariadb:10

export DB_HOST=127.0.0.1 DB_PORT=3306 DB_NAME=news DB_USER=admin DB_PASSWORD=pass

# 3) 마이그레이션 & 개발 서버
python manage.py migrate
python manage.py runserver 0.0.0.0:8000

# 4) 관리 커맨드 테스트
python manage.py crawl_news
```

컨테이너 빌드/실행(로컬):

```bash
docker build -t news-service:dev .

docker run --rm -p 8000:8000 \
  -e DB_HOST=host.docker.internal \
  -e DB_PORT=3306 \
  -e DB_NAME=news \
  -e DB_USER=admin \
  -e DB_PASSWORD=pass \
  news-service:dev
```

---

## 📈 모니터링 & 로깅

- **CloudWatch Logs** 그룹: `/ecs/<service-name>`  
  `aws logs tail /ecs/<service-name> --follow`
- GitHub Actions 로그에서
  - RunTask 결과(ExitCode/StoppedReason) 출력
  - 필요한 경우 해당 **TaskID** 로 CloudWatch 로그 스트림 자동 조회

---

## 🛠️ 트러블슈팅

| 증상 | 원인/해결 |
|---|---|
| `ServiceNotFoundException` (UpdateService 실패) | 서비스가 아직 없음 → 파이프라인의 “Ensure ECS service exists” 단계 활성화 또는 최초 1회 수동 생성 |
| `ResourceInitializationError: unable to pull secrets` | Execution Role에 `secretsmanager:GetSecretValue` 권한 누락. 시크릿 ARN/접근 영역(Region) 확인 |
| ALB HealthCheck `unhealthy` | TargetGroup 타입이 `ip` 인지 확인, 헬스체크 경로/응답 코드(200) 확인, 보안그룹/서브넷 라우팅 점검 |
| 502/504 게이트웨이 | 서비스 태스크가 기동 전/CrashLoop. CloudWatch Logs 또는 `aws ecs describe-tasks` 로 상태 확인 |
| RDS 연결 타임아웃 | RDS SG 인바운드에 ECS 서비스 SG 허용, 서브넷/라우팅(NAT 또는 VPC Endpoint) 점검 |
| ECR Pull 실패 | VPC Endpoint(`ecr.api`, `ecr.dkr`) 또는 NAT 연결 확인, Execution Role에 ECR 권한 포함 |
| `mysqlclient`/`pymysql` 에러 | 이미지에 드라이버 포함 여부 확인, 파이프라인의 DB one-off에서 예외 메시지 확인 |


