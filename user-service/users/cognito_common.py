# users/cognito_common.py
import jwt
from jwt import PyJWKClient
from django.conf import settings
from django.contrib.auth import get_user_model, login

User = get_user_model()
_jwks = PyJWKClient(settings.COGNITO_JWKS_URL)

def decode_and_validate_id_token(id_token: str) -> dict:
    key = _jwks.get_signing_key_from_jwt(id_token).key
    # 허용 client_id를 리스트로 받기
    audiences = getattr(settings, "COGNITO_CLIENT_IDS", [settings.COGNITO_CLIENT_ID])
    claims = jwt.decode(
        id_token,
        key,
        algorithms=["RS256"],
        audience=audiences,
        issuer=settings.COGNITO_ISSUER,
        leeway=60,
    )
    return claims

def upsert_user_and_login(request, claims: dict, tokens: dict):
    email = claims.get("email")
    if not email:
        raise ValueError("email missing in token claims")

    # 토큰/유저정보에서 맵핑
    name  = claims.get("name")
    phone = claims.get("phone_number")
    birth = claims.get("birthdate")
    team  = claims.get("custom:favorite_team") or claims.get("custom:team")

    # 생성 또는 조회
    user = User.objects.filter(email=email).first()
    if not user:
        base = email.split("@")[0]; username = base; i = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{i}"; i += 1
        user = User.objects.create_user(username=username, email=email, password=None)

    # ✅ 값이 있으면 매번 갱신 (이전 값이 있어도 덮어씀)
    if name:
        user.name = name  # 단일 name 필드만 사용 (first_name 제거됨)
    if phone is not None:
        user.tel = phone
    if birth is not None:
        user.birth = birth
    if team is not None:
        user.team = team

    # ✅ Cognito 동기화 상태 리셋: 활성/삭제해제
    if hasattr(user, "cognito_status"):
        user.cognito_status = "active"
    if hasattr(user, "cognito_deleted_at"):
        user.cognito_deleted_at = None

    user.save()

    # 로그인/세션 토큰 저장
    login(request, user)
    request.session["id_token"] = tokens.get("id_token")
    request.session["access_token"] = tokens.get("access_token")
    request.session["refresh_token"] = tokens.get("refresh_token")
    request.session["id_token_exp"] = claims.get("exp")
    return user


