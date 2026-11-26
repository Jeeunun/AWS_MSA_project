# users/views_custom.py
import hmac, hashlib, base64, boto3, re
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.utils import timezone

from .cognito_common import decode_and_validate_id_token, upsert_user_and_login


# ---------- boto3 클라이언트 ----------
def _cognito_client():
    profile = getattr(settings, "AWS_PROFILE", None)
    region = getattr(settings, "AWS_REGION", "ap-northeast-2")
    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    return session.client("cognito-idp", region_name=region)


# ---------- SecretHash ----------
def _secret_hash(username: str) -> str:
    client_id = getattr(settings, "COGNITO_CUSTOM_CLIENT_ID", settings.COGNITO_CLIENT_ID)
    client_secret = getattr(settings, "COGNITO_CUSTOM_CLIENT_SECRET", settings.COGNITO_CLIENT_SECRET)
    key = client_secret.encode("utf-8")
    msg = (username + client_id).encode("utf-8")
    digest = hmac.new(key, msg, hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


# ---------- 공용 헬퍼: 로컬 사용자 deleted 마킹 ----------
def _mark_local_deleted(email: str):
    U = get_user_model()
    u = U.objects.filter(email=email).first()
    if u and getattr(u, "cognito_status", None) != "deleted":
        u.cognito_status = "deleted"
        u.cognito_deleted_at = timezone.now()
        u.save(update_fields=["cognito_status", "cognito_deleted_at"])
        print("[CUSTOM] marked local user as deleted:", u.email)


# ---------- 폼 페이지 ----------
def custom_signup_page(request):
    return render(request, "registration/custom_signup.html")

def custom_login_page(request):
    return render(request, "registration/custom_login.html")


# ---------- 가입 제출 ----------
@require_http_methods(["POST"])
def custom_signup_submit(request):
    email = (request.POST.get("email") or "").strip()
    password = (request.POST.get("password") or "")
    name = (request.POST.get("name") or "").strip() or (email.split("@")[0] if email else "")
    phone = (request.POST.get("phone_number") or "").strip()
    birth = (request.POST.get("birthdate") or "").strip()
    team  = (request.POST.get("custom:favorite_team") or "").strip()

    print("[CUSTOM SIGNUP] VALUES:", {
        "email": email, "password_len": len(password),
        "phone_number": phone, "birthdate": birth, "custom:favorite_team": team
    })

    if not email or not password:
        return HttpResponseBadRequest("missing: email/password")

    # 010xxxxxxxx → +8210xxxxxxxx (선택)
    if phone and re.fullmatch(r"0\d{9,10}", re.sub(r"\D", "", phone)):
        digits = re.sub(r"\D", "", phone)
        phone = "+82" + digits[1:]

    if team.lower() == "none":
        team = ""

    client_id = getattr(settings, "COGNITO_CUSTOM_CLIENT_ID", settings.COGNITO_CLIENT_ID)
    client = _cognito_client()

    attrs = [{"Name": "email", "Value": email}, {"Name": "name", "Value": name}]
    if phone: attrs.append({"Name": "phone_number", "Value": phone})
    if birth: attrs.append({"Name": "birthdate", "Value": birth})
    if team:  attrs.append({"Name": "custom:favorite_team", "Value": team})

    try:
        client.sign_up(
            ClientId=client_id,
            SecretHash=_secret_hash(email),
            Username=email,
            Password=password,
            UserAttributes=attrs,
        )
        print("[CUSTOM SIGNUP] sign_up OK → confirm")
        messages.success(request, "인증코드를 이메일로 보냈습니다. 인증 후 로그인하세요.")
        return redirect("/users/custom/confirm")
    except client.exceptions.UsernameExistsException:
        return HttpResponseBadRequest("sign_up failed: username/email already exists")
    except Exception as e:
        print("[CUSTOM SIGNUP] ERROR:", e)
        return HttpResponseBadRequest(f"sign_up failed: {e}")


# ---------- 인증코드 확인(가입 확인 + 로컬 DB 즉시 저장) ----------
@require_http_methods(["GET", "POST"])
def custom_confirm(request):
    if request.method == "GET":
        return render(request, "registration/custom_confirm.html")

    email = (request.POST.get("email") or "").strip()
    code  = (request.POST.get("code") or "").strip()
    if not email or not code:
        return HttpResponseBadRequest("missing email/code")

    client_id = getattr(settings, "COGNITO_CUSTOM_CLIENT_ID", settings.COGNITO_CLIENT_ID)
    client = _cognito_client()

    try:
        client.confirm_sign_up(
            ClientId=client_id,
            SecretHash=_secret_hash(email),
            Username=email,
            ConfirmationCode=code,
        )
        print("[CUSTOM CONFIRM] confirm_sign_up OK")

        ui = client.admin_get_user(
            UserPoolId=settings.COGNITO_USER_POOL_ID,
            Username=email,
        )
        attr_map = {a["Name"]: a["Value"] for a in ui.get("UserAttributes", [])}
        name  = attr_map.get("name")
        phone = attr_map.get("phone_number")
        birth = attr_map.get("birthdate")
        team  = attr_map.get("custom:favorite_team") or attr_map.get("custom:team")

        U = get_user_model()
        user = U.objects.filter(email=email).first()
        if not user:
            base = email.split("@")[0]; username = base; i = 1
            while U.objects.filter(username=username).exists():
                username = f"{base}{i}"; i += 1
            user = U.objects.create_user(username=username, email=email, password=None)

        if name:  user.name  = name
        if phone: user.tel   = phone
        if birth: user.birth = birth
        if team:  user.team  = team
        user.cognito_status = "active"
        user.cognito_deleted_at = None
        user.save()
        print("[CUSTOM CONFIRM] local user upsert OK:", user.id, user.email)

        messages.success(request, "인증이 완료되었습니다. 이제 로그인하세요.")
        return redirect("/users/custom/login")

    except client.exceptions.CodeMismatchException:
        return HttpResponseBadRequest("confirm failed: wrong code")
    except client.exceptions.ExpiredCodeException:
        return HttpResponseBadRequest("confirm failed: code expired")
    except client.exceptions.UserNotFoundException:
        return HttpResponseBadRequest("confirm failed: user not found")
    except client.exceptions.NotAuthorizedException as e:
        print("[CUSTOM CONFIRM] NotAuthorized:", e)
        return HttpResponseBadRequest("confirm failed: not authorized (check IAM permissions)")
    except Exception as e:
        print("[CUSTOM CONFIRM] ERROR:", e)
        return HttpResponseBadRequest(f"confirm failed: {e}")


# ---------- 로그인 (USER_PASSWORD_AUTH) ----------
@require_http_methods(["POST"])
def custom_signin(request):
    email = (request.POST.get("email") or "").strip()
    password = (request.POST.get("password") or "")
    if not email or not password:
        return HttpResponseBadRequest("missing email/password")

    client_id = getattr(settings, "COGNITO_CUSTOM_CLIENT_ID", settings.COGNITO_CLIENT_ID)
    client = _cognito_client()

    try:
        resp = client.initiate_auth(
            ClientId=client_id,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": email,
                "PASSWORD": password,
                "SECRET_HASH": _secret_hash(email),
            },
        )
        ar = resp["AuthenticationResult"]
        tokens = {
            "id_token": ar["IdToken"],
            "access_token": ar["AccessToken"],
            "refresh_token": ar.get("RefreshToken"),
        }
        print("[CUSTOM SIGNIN] initiate_auth OK")

        claims = decode_and_validate_id_token(tokens["id_token"])

        needed = {"name", "phone_number", "birthdate", "custom:favorite_team", "custom:team"}
        if not needed.issubset(claims.keys()):
            try:
                ui = client.get_user(AccessToken=tokens["access_token"])
                attr_map = {a["Name"]: a["Value"] for a in ui.get("UserAttributes", [])}
                claims.setdefault("name", attr_map.get("name"))
                claims.setdefault("phone_number", attr_map.get("phone_number"))
                claims.setdefault("birthdate", attr_map.get("birthdate"))
                claims.setdefault("custom:favorite_team",
                                  attr_map.get("custom:favorite_team") or attr_map.get("custom:team"))
            except Exception as get_e:
                print("[CUSTOM SIGNIN] get_user warning:", get_e)

        user = upsert_user_and_login(request, claims, tokens)
        print("[CUSTOM SIGNIN] upsert/login OK → local user:", getattr(user, "id", None), getattr(user, "email", None))

        target = getattr(settings, "CLOUDFRONT_MAIN_URL", None) or "/"
        print("[CUSTOM SIGNIN] redirect to:", target)
        return redirect(target)

    except client.exceptions.UserNotFoundException:
        _mark_local_deleted(email)
        return HttpResponseBadRequest("signin failed: user not found")

    except client.exceptions.NotAuthorizedException as e:
        # 삭제/미존재도 이 예외가 올 수 있으므로 추가 확인
        try:
            client.admin_get_user(
                UserPoolId=settings.COGNITO_USER_POOL_ID,
                Username=email,
            )
            # 존재하면 진짜 비밀번호 오류
            return HttpResponseBadRequest("signin failed: incorrect username or password")
        except (client.exceptions.UserNotFoundException,
                client.exceptions.ResourceNotFoundException):
            _mark_local_deleted(email)
            return HttpResponseBadRequest("signin failed: user deleted or not found")
        except Exception as probe_e:
            print("[CUSTOM SIGNIN] probe admin_get_user failed:", probe_e)
            return HttpResponseBadRequest("signin failed: incorrect username or password")

    except client.exceptions.UserNotConfirmedException:
        return HttpResponseBadRequest("signin failed: user not confirmed")
    except Exception as e:
        print("[CUSTOM SIGNIN] ERROR:", e)
        return HttpResponseBadRequest(f"signin failed: {e}")






