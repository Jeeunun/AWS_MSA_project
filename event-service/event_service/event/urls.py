from django.urls import path
from . import views

# urlpatterns = [
#     path('result', views.result_view, name='result'),
#     path('rank', views.rank_all_view, name='rank'),
# ]

app_name = 'events'

urlpatterns = [
    path('', views.dashboard, name='home'),
    path('participate/', views.participate_view, name='participate'),
    path('results/', views.result_view, name='results'),
    path('ranks/', views.rank_all_view, name='ranks'),
    path("participate/vote/", views.vote_api, name="vote_api"),
]