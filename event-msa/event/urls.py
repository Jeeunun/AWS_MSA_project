from django.urls import path
from django.http import HttpResponse
from . import views, api_views

def healthz(_):
    return HttpResponse("ok")

app_name = "events"

urlpatterns = [
    # === REST API 엔드포인트 (React 연동용) ===
    path('api/event/schedules/', api_views.schedule_list_api, name='api_schedules'),
    path('api/event/participate/', api_views.participate_api, name='api_participate'),
    path('api/event/vote/', api_views.vote_api, name='api_vote'),
    path('api/event/coupons/', api_views.coupons_api, name='api_coupons'),
    path('api/event/ranks/', api_views.ranks_api, name='api_ranks'),
    path('api/event/user-history/', api_views.user_history_api, name='api_user_history'),
    path('api/event/delete-user-data/', api_views.delete_user_data_api, name='api_delete_user_data'),
    
    # === 기존 HTML 뷰 (템플릿용, 선택적 유지) ===
    path("auth/tokens/", views.debug_tokens, name="debug_tokens"),  # 개발용
    path('event/', views.schedule_view, name='home'), 
    path('participate/', views.participate_view, name='participate'),
    path('coupon/', views.coupon_view, name='coupons'),
    path('schedule/', views.schedule_view, name='schedules'),
    path('ranks/', views.rank_all_view, name='ranks'),
    # path("participate/vote/", views.vote_api, name="vote_api"),  # 기존 투표 API (주석 처리)
    
    # === 헬스체크 ===
    path("healthz", healthz),
]