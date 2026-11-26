import os
from pathlib import Path
from dotenv import load_dotenv

# 실행 포트 설정
PORT = 8004

# .env 파일 로드
load_dotenv()
# env.txt 파일도 로드 (백업용)
load_dotenv('env.txt')

# PyMySQL을 MySQL 백엔드로 사용 (가장 먼저 실행되어야 함)
try:
    import pymysql
    pymysql.install_as_MySQLdb()
    print("PyMySQL을 MySQL 백엔드로 설정 완료")
except ImportError:
    print("경고: PyMySQL이 설치되지 않았습니다. mysqlclient를 설치하세요.")

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-df2+!_wd(wt@hrg=5q1@v*g3(k0d(%xtf9*6dhl)+(+9i@y-op')"

# 환경변수에서 데이터베이스 설정 가져오기
DB_NAME = os.environ.get('DB_NAME', 'info_db')
DB_USER = os.environ.get('DB_USER', 'root')  # 기본값을 'kbo_user'로 변경
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'soldesk12!!')  # 기본값을 'test'로 변경
DB_HOST = os.environ.get('DB_HOST', 'localhost')  # localhost 대신 실제 MySQL 서버 IP
DB_PORT = os.environ.get('DB_PORT', '3306')

# 데이터베이스 설정 확인 및 로깅
print(f"=== Django 데이터베이스 설정 ===")
print(f"DB_NAME: {DB_NAME}")
print(f"DB_USER: {DB_USER}")
print(f"DB_PASSWORD: {'*' * len(DB_PASSWORD) if DB_PASSWORD else '설정되지 않음'}")
print(f"DB_HOST: {DB_HOST}")
print(f"DB_PORT: {DB_PORT}")
print(f"환경변수 DB_USER: {os.environ.get('DB_USER', '설정되지 않음')}")
print(f"환경변수 DB_PASSWORD: {os.environ.get('DB_PASSWORD', '설정되지 않음')}")
print("=" * 30)

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
DEBUG = os.environ.get('DEBUG', 'True').lower() in ['1', 'true', 'yes']
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

# API Gateway 도메인 추가
if '42z6qi4fnd.execute-api.ap-northeast-2.amazonaws.com' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('42z6qi4fnd.execute-api.ap-northeast-2.amazonaws.com')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'kbo',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'kbo_crawler.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'kbo_crawler.wsgi.application'
ASGI_APPLICATION = 'kbo_crawler.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO'",
            'autocommit': True,
        },
    }
}

# SQLite 설정 (개발용, 주석 처리)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = False

# 정적 파일 설정
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / 'kbo' / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# 미디어 파일 설정
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# 보안 설정 (최소한)
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False
X_FRAME_OPTIONS = 'DENY'

# 로깅 설정
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# 정적 파일 수집 경로
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS 설정 (환경변수에서 읽어오기)
CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS', 
    'https://d18wspy7xouagh.cloudfront.net,http://localhost:5173,http://127.0.0.1:5173'
).split(',')

CORS_ALLOW_CREDENTIALS = os.environ.get('CORS_ALLOW_CREDENTIALS', 'True').lower() in ['1', 'true', 'yes']

# CORS 추가 헤더 허용
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# CORS 추가 메서드 허용
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# REST Framework 설정
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'kbo.cognito_auth.CognitoJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
}

# Python 3.13 호환성을 위한 설정
import sys
if sys.version_info >= (3, 13):
    # Python 3.13+ 에서는 일부 기능이 기본적으로 활성화됨
    pass