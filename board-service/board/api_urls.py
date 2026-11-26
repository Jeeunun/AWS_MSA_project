from django.urls import path
from . import api_views

urlpatterns = [
    # 게시글 관련 API
    path('posts/', api_views.post_list_api, name='post_list_api'),
    path('posts/create/', api_views.post_create_api, name='post_create_api'),
    path('posts/<int:pk>/', api_views.post_detail_api, name='post_detail_api'),
    path('posts/<int:pk>/update/', api_views.post_update_api, name='post_update_api'),
    path('posts/<int:pk>/delete/', api_views.post_delete_api, name='post_delete_api'),
    
    # 댓글 관련 API
    path('posts/<int:post_pk>/comments/', api_views.comment_create_api, name='comment_create_api'),
    path('posts/<int:post_pk>/comments/<int:comment_pk>/', api_views.comment_update_api, name='comment_update_api'),
    path('posts/<int:post_pk>/comments/<int:comment_pk>/delete/', api_views.comment_delete_api, name='comment_delete_api'),
]
