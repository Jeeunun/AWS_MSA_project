from django.urls import path
from django.http import HttpResponse
from . import views, api_views

def healthz():
    return HttpResponse("OK")

app_name = "info"

urlpatterns = [
    # === REST API 엔드포인트 (React 연동용) ===
    path('teams/', api_views.teams_list_api, name='api_teams'),
    path('teams/options/', api_views.teams_options_api, name='api_teams_options'),
    path('teams/compare/', api_views.team_comparison_api, name='api_teams_compare'),
    path('teams/<str:team_code>/', api_views.team_detail_api, name='api_team_detail'),
    path('players/search/', api_views.players_search_api, name='api_players_search'),
    path('players/<int:player_id>/', api_views.player_detail_api, name='api_player_detail'),
    path('positions/options/', api_views.positions_options_api, name='api_positions_options'),
    path('stats/analysis/', api_views.stats_analysis_api, name='api_stats_analysis'),
    
    # === 기존 HTML 뷰 (템플릿용, 선택적 유지) ===
    path('page/', views.team_list, name='teams_main'),
    path('page/teams/<str:code>/', views.team_detail, name='team_detail'),
    path('page/search/', views.search_advanced, name='search_advanced'),
    path('page/stats/', views.stats_analysis, name='stats_analysis'),
    path('page/compare/', views.team_comparison, name='team_comparison'),
    path('page/player/<int:player_id>/modal/', views.player_detail_modal, name='player_detail_modal'),
    
    # === 헬스체크 ===
    path('healthz', healthz),
]