# news/urls.py
from django.urls import path
from django.http import HttpResponse
from .views import news_list
from . import api_views

def healthz(_):
    return HttpResponse("ok")

app_name = "news"

urlpatterns = [
    # === REST API 엔드포인트 (React 연동용) ===
    path('api/news/', api_views.news_list_api, name='api_news_list'),
    path('api/news/<int:news_id>/', api_views.news_detail_api, name='api_news_detail'),
    path('api/news/search/', api_views.news_search_api, name='api_news_search'),
    path('api/news/categories/', api_views.news_categories_api, name='api_news_categories'),
    path('api/news/today/', api_views.news_today_api, name='api_news_today'),
    
    # === 기존 HTML 뷰 (템플릿용, 선택적 유지) ===
    path('news/', news_list, name='news_list'),
    
    # === 헬스체크 ===
    path('healthz', healthz),
]
