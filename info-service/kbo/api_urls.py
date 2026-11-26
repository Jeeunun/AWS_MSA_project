from django.urls import path
from . import api_views

urlpatterns = [
    # === React 연동용 REST API 엔드포인트 ===
    path('teams/', api_views.teams_list_api, name='api_teams_list'),
    path('teams/options/', api_views.teams_options_api, name='api_teams_options'),
    path('teams/compare/', api_views.team_comparison_api, name='api_team_comparison'),
    path('teams/<str:team_code>/', api_views.team_detail_api, name='api_team_detail'),
    path('players/search/', api_views.players_search_api, name='api_players_search'),
    path('players/<int:player_id>/', api_views.player_detail_api, name='api_player_detail'),
    path('positions/options/', api_views.positions_options_api, name='api_positions_options'),
    path('stats/analysis/', api_views.stats_analysis_api, name='api_stats_analysis'),
]
