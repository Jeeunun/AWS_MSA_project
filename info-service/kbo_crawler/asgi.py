"""
ASGI config for kbo_crawler project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

# PyMySQL을 MySQL 백엔드로 사용 (Django 설정보다 먼저 실행)
try:
    import pymysql
    pymysql.install_as_MySQLdb()
    print("asgi.py: PyMySQL을 MySQL 백엔드로 설정 완료")
except ImportError:
    print("asgi.py: 경고: PyMySQL이 설치되지 않았습니다.")

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kbo_crawler.settings')

application = get_asgi_application()