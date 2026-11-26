from django.urls import path
from . import views
from . import views_custom   # 반드시 추가되어 있어야 함

urlpatterns = [
    # Hosted UI (기존)
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('auth/callback', views.cognito_callback, name='cognito_callback'),
    path('auth/loggedout', views.cognito_loggedout, name='cognito_loggedout'),
    path('logout/', views.logout_view, name='logout'),

    # 커스텀 UI (페이지)
    path('custom/signup',  views_custom.custom_signup_page, name='custom_signup_page'),
    path('custom/login',   views_custom.custom_login_page,  name='custom_login_page'),
    path('custom/confirm', views_custom.custom_confirm,     name='custom_confirm'),  # GET/POST

    # 커스텀 UI (제출)
    path('custom/signup/submit', views_custom.custom_signup_submit, name='custom_signup_submit'),
    path('custom/login/submit',  views_custom.custom_signin,        name='custom_signin'),

    # 프로필
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('password/change/', views.PasswordChangeViewWithPopup.as_view(), name='password_change'),
]




