FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Seoul

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      ca-certificates tzdata dos2unix mariadb-client curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 컨텍스트(news-service/) 기준
COPY requirements.txt .
RUN python -m pip install -U pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# 앱 전체 복사
COPY . /app

EXPOSE 8003

# 스크립트 파일 복사 및 줄바꿈 문자 변환
COPY ./entrypoint-migrate.sh /app/
COPY ./entrypoint-web.sh /app/

# Windows 줄바꿈 문자를 Unix 형식으로 변환하고 실행 권한 부여
RUN dos2unix /app/entrypoint-migrate.sh /app/entrypoint-web.sh && \
    chmod +x /app/entrypoint-migrate.sh /app/entrypoint-web.sh

CMD ["gunicorn","news_service.wsgi:application","--bind","0.0.0.0:8003","--workers","3","--timeout","120"]
