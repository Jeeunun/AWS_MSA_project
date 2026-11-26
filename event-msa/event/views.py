from django.shortcuts import render
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import date, datetime, time as time_cls
from .models import Schedule,  Predict, Coupon, TotalRank, AttackRank, DefenseRank
import secrets, string
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Count, Min
from django.db import IntegrityError, transaction
from django.conf import settings
import requests
import secrets, hashlib, base64, requests, json
from django.urls import reverse
from django.shortcuts import redirect
from django.http import JsonResponse, HttpResponse
import urllib.parse as up
from django.http import JsonResponse, HttpResponseNotFound
from django.views.decorators.http import require_GET


# Cognito 설정을 settings.py에서 가져옴 (OAuth 제거됨)
from django.conf import settings

def _decode_jwt_payload(jwt: str) -> dict:
    """서명 검증 없이 payload만 base64url decode (개발/표시용)"""
    if not jwt or "." not in jwt:
        return {}
    try:
        payload = jwt.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload.encode()).decode())
    except Exception:
        return {}


def schedule_view(request):
    """
    경기일정/결과
    - 기본: 최신 날짜부터 정렬
    - ?date=YYYY-MM-DD 로 특정 일자 필터
    """
    # 1) 폼의 name="date" 를 그대로 읽기
    q_date = request.GET.get("date")

    # 2) 기본 쿼리
    qs = Schedule.objects.all().order_by("match_date", "startTime")

    # 3) 'YYYY-MM-DD' 형식만 필터에 반영 (모델 필드는 match_date)
    if q_date:
        try:
            day = date.fromisoformat(q_date)   
            qs = qs.filter(match_date=day)        
        except ValueError:
            pass  # 잘못된 값이면 무시

    # 4) 페이지네이션
    page = request.GET.get("page", 1)
    schedules = Paginator(qs, 20).get_page(page)

    # 5) 템플릿과 변수명 일치 (템플릿은 {% for g in schedules %})
    return render(request, "events/schedule.html", {
        "schedules": schedules,                    # 키 이름 통일
        "selected_date": q_date,                   # input 값 바인딩
        "today": timezone.localdate(),
    })


def _token_id(request) -> int:
    if request.user.is_authenticated:
        return request.user.id
    if "event_token_id" not in request.session:
        request.session["event_token_id"] = int(timezone.now().timestamp())
        request.session.save()
    return request.session["event_token_id"]



def participate_view(request):
    """현재 시점 기준 가장 가까운 '경기전' 경기 중 하나만 랜덤으로 노출 + 내 참여내역"""

    now = timezone.localdate()
    base = Schedule.objects.filter(gameStatus="BEFORE", match_date__gte=now).order_by("match_date")
    match = None
    if base.exists():
        nearest = base.first().match_date
        match = base.filter(match_date=nearest).order_by("?").first()

    token_id = _token_id(request)
    id_token = request.session.get('id_token') or ""
    access_token = request.session.get("access_token") or ""
    history = (Predict.objects
               .filter(token_id=token_id)
               .select_related("schedule")
               .order_by("-schedule__match_date")[:20])

    agg = {"away": 0, "home": 0, "total": 0}
    if match:
        for r in (Predict.objects.filter(schedule=match)
                  .values("predicted").annotate(c=Count("idx"))):
            if r["predicted"] == "AWAY": agg["away"] = r["c"]
            if r["predicted"] == "HOME": agg["home"] = r["c"]
        agg["total"] = agg["away"] + agg["home"]

    return render(request, "events/participate.html", {
        "match": match, "history": history, "agg": agg, "now": now,
        "id_token": id_token, "access_token" : access_token,
    })

def _coupon_code(n=12):
    import string, secrets
    abc = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(abc) for _ in range(n))

def coupon_view(request):
    """
    쿠폰 현황 페이지 : user_id(=cognito_sub) 기준 내 쿠폰 조회
    """

    # 사용자 표시용 정보 (ID 토큰에서 name/email/sub를 우선 사용)
    claims = _decode_jwt_payload(request.session.get("id_token") or "")
    display_name = claims.get("name") or claims.get("email") or getattr(request.user, "username", None) or "사용자"
    user_id = claims.get("sub") or (str(request.user.id) if request.user.is_authenticated else None)
    
    # 기본값 초기화, 있으면 덮어쓰기
    coupons_qs = Coupon.objects.none()
    total_count = 0

    if user_id:
        coupons_qs = Coupon.objects.select_related("predict").filter(predict_user_id=user_id).order_by("-created_at")
        total_count = coupons_qs.count()

    ctx = {
            "display_name": display_name,
            "user_id": user_id,
            "coupons": coupons_qs,
            "total_count": total_count,
            "now": timezone.now(),
    }
    return render(request, "events/coupon.html", ctx)

# 토큰값을 프론트에서 보기 위해 (개발용함수 / 운영에선 삭제하기!!)
@require_POST
@require_POST
def vote_api(request):
    def j(data, status=200):
        # 한글 그대로 내려가도록
        return JsonResponse(data, status=status, json_dumps_params={'ensure_ascii': False})

    # 1) 입력 검증
    result_id = request.POST.get("result_id")
    choice    = request.POST.get("choice")
    if not result_id or not str(result_id).isdigit():
        return j({"ok": False, "msg": "잘못된 요청(result_id 누락)"}, 400)
    if choice not in ("AWAY", "HOME"):
        return j({"ok": False, "msg": "잘못된 선택"}, 400)

    # 2) 경기 로드
    from .models import Schedule, Predict  # 경로 맞게
    try:
        match = Schedule.objects.get(pk=int(result_id))
    except Schedule.DoesNotExist:
        return j({"ok": False, "msg": "경기를 찾을 수 없습니다."}, 404)

    # 3) 시작 시간(날짜+시간) 기준 차단
    try:
        h, m = map(int, (match.startTime or "00:00").strip().split(":"))
    except Exception:
        h, m = 0, 0
    start_naive = datetime.combine(match.match_date, time_cls(hour=h, minute=m))
    start_dt = timezone.make_aware(start_naive, timezone.get_current_timezone())

    if timezone.now() >= start_dt or match.gameStatus != "BEFORE":
        return j({"ok": False, "msg": "경기가 시작되어 참여할 수 없습니다."}, 409)

    # 4) 하루 1회 제한 (같은 날짜 다른 경기 포함)
    token_id = _token_id(request)
    if Predict.objects.filter(token_id=token_id, schedule__match_date=match.match_date).exists():
        return j({"ok": False, "msg": "오늘은 이미 참여하셨어요."}, 409)

    # 5) 저장 (동시 요청 대비 DB 유니크가 있다면 IntegrityError로 잡기)
    try:
        with transaction.atomic():
            Predict.objects.create(
                token_id=token_id,
                predicted=choice,
                schedule=match,
                # match_date를 비정규화 컬럼으로 쓰는 경우: match_date=match.match_date
            )
    except IntegrityError:
        # 유니크 제약(예: token_id + match_date)이 있는 경우
        return j({"ok": False, "msg": "오늘은 이미 참여하셨어요."}, 409)
    except Exception as e:
        # 개발 중엔 에러 내용을 보여 주고, 운영에선 일반 메시지
        msg = str(e) if settings.DEBUG else "서버 오류가 발생했습니다."
        return j({"ok": False, "msg": msg}, 500)

    return j({"ok": True, "msg": "이벤트 참여 완료!"})

@require_GET
def debug_tokens(request):
    # 운영에서 노출 금지
    if not settings.DEBUG:
      return HttpResponseNotFound()

    return JsonResponse({
        "has_tokens": bool(request.session.get("id_token")),
        "id_token": request.session.get("id_token"),
        "access_token": request.session.get("access_token"),
    }, json_dumps_params={'ensure_ascii': False})

def rank_all_view(request):
    """
    종합/공격/수비 순위 한 페이지에 표f시
    """
    total = TotalRank.objects.all().order_by('rank')
    attack = AttackRank.objects.all().order_by('rank')
    defend = DefenseRank.objects.all().order_by('rank')

    return render(request, 'events/rank.html', {
        'total': total, 'attack': attack, 'defend': defend
    })