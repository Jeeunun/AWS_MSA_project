# users/views.py
import base64, hashlib, os, requests, jwt
from jwt import PyJWKClient
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth import login, logout, get_user_model
from django.http import HttpResponseBadRequest
from urllib.parse import urlencode

from .forms import SignupForm, ProfileForm, CustomPasswordChangeForm

User = get_user_model()

# ----- PKCE helpers -----
def _new_pkce():
    verifier = base64.urlsafe_b64encode(os.urandom(40)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return verifier, challenge

# =======================
# Hosted UI: 로그인/회원가입 진입
# =======================
def login_view(request):
    verifier, challenge = _new_pkce()
    request.session["pkce_verifier"] = verifier

    
    params = {
        "client_id": settings.COGNITO_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.COGNITO_REDIRECT_URI,
        "scope": "openid email profile",   # 공백 구분
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    authorize = f"{settings.COGNITO_DOMAIN}/oauth2/authorize?{urlencode(params)}"
    print("AUTH URL =>", authorize)  # 콘솔 확인용
    return redirect(authorize)


def signup_view(request):
    # 회원가입도 Hosted UI가 처리 -> 로그인과 동일 흐름으로 보냄
    return login_view(request)

# =======================
# Hosted UI 콜백: code -> token 교환 + ID 토큰 검증 + 로컬 DB 연동
# =======================
def cognito_callback(request):
    code = request.GET.get("code")
    if not code:
        err = request.GET.get("error_description") or "Missing code"
        return HttpResponseBadRequest(err)

    verifier = request.session.get("pkce_verifier")
    if not verifier:
        return HttpResponseBadRequest("Missing PKCE verifier")

    # 1) 토큰 교환
    token_url = f"{settings.COGNITO_DOMAIN}/oauth2/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": settings.COGNITO_CLIENT_ID,
        "code": code,
        "redirect_uri": settings.COGNITO_REDIRECT_URI,
        "code_verifier": verifier,
    }

    # Authorization 헤더에 client_id + client_secret 추가
    basic_auth = base64.b64encode(
        f"{settings.COGNITO_CLIENT_ID}:{settings.COGNITO_CLIENT_SECRET}".encode()
    ).decode()

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {basic_auth}"
    }

    res = requests.post(token_url, data=data, headers=headers)
    if res.status_code != 200:
        return HttpResponseBadRequest(f"Token exchange failed: {res.text}")

    tokens = res.json()
    id_token = tokens.get("id_token")
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")


    # 2) ID 토큰 검증(JWKS, iss/aud)
    jwks_client = PyJWKClient(settings.COGNITO_JWKS_URL)
    signing_key = jwks_client.get_signing_key_from_jwt(id_token).key
    claims = jwt.decode(
        id_token,
        signing_key,
        algorithms=["RS256"],
        audience=settings.COGNITO_CLIENT_ID,
        issuer=settings.COGNITO_ISSUER,
        leeway=60  # 최대 60초 시간차 허용
    )


    # 3) 클레임 추출
    email = claims.get("email")
    name = claims.get("name")  # Hosted UI에서 입력한 이름
    phone = claims.get("phone_number")  # +821012345678 (E.164)
    birthdate = claims.get("birthdate")  # YYYY-MM-DD
    team = claims.get("custom:favorite_team") or claims.get("custom:team")

    if not email:
        return HttpResponseBadRequest("No email in token claims")

    # 4) 로컬 사용자 생성/업데이트 (이메일 기준)
    user = User.objects.filter(email=email).first()
    if not user:
        base_username = email.split("@")[0]
        username = base_username
        i = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{i}"
            i += 1
        user = User.objects.create_user(
            username=username,
            email=email,
            password=None,  # 비밀번호는 Cognito가 관리
        )

    # 이름/전화/생년/팀 매핑 (있는 값만 반영)
    if name and not user.first_name:
        user.first_name = name
    if phone:
        user.tel = phone
    if birthdate:
        # 모델은 문자열 컬럼이니 우선 원본 저장(필요시 YYMMDD로 가공 로직 추가 가능)
        user.birth = birthdate
    if team:
        user.team = team
    user.save()

    # 5) Django 세션 로그인 + 토큰 보관(필요시)
    login(request, user)
    request.session["id_token"] = id_token
    request.session["access_token"] = access_token
    request.session["refresh_token"] = refresh_token
    request.session["id_token_exp"] = claims.get("exp")

    messages.success(request, f"{email}님 환영합니다.")
    return redirect("https://dwreytuh5uwv5.cloudfront.net/test_main.html")  # 로그인 후 메인으로

# =======================
# 로그아웃
# =======================
def logout_view(request):
    logout(request)
    logout_url = (
        f"{settings.COGNITO_DOMAIN}/logout"
        f"?client_id={settings.COGNITO_CLIENT_ID}"
        f"&logout_uri={settings.COGNITO_LOGOUT_REDIRECT_URI}"
    )
    return redirect(logout_url)

def cognito_loggedout(request):
    messages.info(request, "정상적으로 로그아웃되었습니다.")
    return redirect("/")

# =======================
# 기존 화면들
# =======================
def home_view(request):
    return render(request, 'home.html')

@login_required
def profile_view(request):
    return render(request, 'users/profile.html', {'user_obj': request.user})

@login_required
def profile_edit_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '내 정보가 저장되었습니다.')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'users/profile_edit.html', {'form': form})

class PasswordChangeViewWithPopup(PasswordChangeView):
    template_name = 'registration/password_change_form.html'
    form_class = CustomPasswordChangeForm
    success_url = reverse_lazy('password_change')  # 같은 페이지로 이동
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "비밀번호가 변경되었습니다.")
        return response



