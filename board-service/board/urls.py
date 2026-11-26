from django.urls import path
from . import views # 현재 디렉토리의 views.py 가져오기

urlpatterns = [
    path('', views.post_list, name='post_list'), # /board/ 또는 / 접속 시 게시물 목록
    path('<int:pk>/', views.post_detail, name='post_detail'), # /board/1/, /board/2/ 등 게시물 상세
    path('new/', views.post_new, name='post_new'), # /board/new/ 새 글 작성
    path('<int:pk>/edit/', views.post_edit, name='post_edit'), # /board/1/edit/ 게시물 수정
    path('<int:pk>/delete/', views.post_delete, name='post_delete'), # /board/1/delete/ 게시물 삭제
    path('<int:pk>/pin/', views.post_toggle_pin, name='post_toggle_pin'), # /board/1/pin/ 게시물 고정/해제
    
    # 댓글 인플레이스 편집/삭제 (AJAX)
    path('comment/<int:pk>/update-ajax/', views.comment_update_ajax, name='comment_update_ajax'),
    path('comment/<int:pk>/delete-ajax/', views.comment_delete_ajax, name='comment_delete_ajax'),

    # 로그인 후 리다이렉션될 콜백 URL (로컬 테스트 시 주석 처리)
    # path('callback/', views.cognito_callback, name='cognito_callback'),
]