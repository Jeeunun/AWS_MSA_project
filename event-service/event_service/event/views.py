from django.shortcuts import render
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime
from .models import Result, TotalRank, AttackRank, DefendRank
import secrets, string
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Count, Min
from .models import Result, Predict, Coupon
# Create your views here.
# def result_view(request):
#     results = Result.objects.all()
#     return render(request, 'events/result.html',{'results': results})

# def rank_all_view(request):
#     total = TotalRank.objects.all()
#     attack = AttackRank.objects.all()
#     defend = DefendRank.objects.all()

#     return render(request, 'events/rank.html', {'total':total, 'attack': attack, 'defend': defend})


def dashboard(request):
    """사이드바 기본 랜딩"""
    return render(request, 'events/dashboard.html')

def participate_view(request):
    """이벤트 참여(페이지 뼈대)"""
    return render(request, 'events/participate.html')

def result_view(request):
    """
    경기일정/결과
    - 기본: 최신 날짜부터 정렬
    - ?date=YYYY-MM-DD 로 특정 일자 필터
    """
    qs = Result.objects.all().order_by('date', 'start_time', 'home_team', 'away_team')

    q_date = request.GET.get('date')
    if q_date:
        try:
            day = datetime.strptime(q_date, "%Y-%m-%d").date()
            qs = qs.filter(date__date=day)
        except ValueError:
            pass

    paginator = Paginator(qs, 30)
    page = request.GET.get('page')
    results = paginator.get_page(page)

    context = {
        'results': results,
        'today': timezone.localtime().date(),
        'selected_date': q_date or '',
    }
    return render(request, 'events/result.html', context)


def _token_id(request) -> int:
    if request.user.is_authenticated:
        return request.user.id
    if "event_token_id" not in request.session:
        request.session["event_token_id"] = int(timezone.now().timestamp())
        request.session.save()
    return request.session["event_token_id"]

def participate_view(request):
    """현재 시점 기준 가장 가까운 '경기전' 경기 중 하나만 랜덤으로 노출 + 내 참여내역"""
    now = timezone.localtime()
    base = Result.objects.filter(status="경기전", date__gte=now).order_by("date")
    match = None
    if base.exists():
        nearest = base.first().date
        match = base.filter(date=nearest).order_by("?").first()

    token_id = _token_id(request)
    history = (Predict.objects
               .filter(token_id=token_id)
               .select_related("result")
               .order_by("-date")[:20])

    agg = {"away": 0, "home": 0, "total": 0}
    if match:
        for r in (Predict.objects.filter(result=match)
                  .values("predicted").annotate(c=Count("idx"))):
            if r["predicted"] == "AWAY": agg["away"] = r["c"]
            if r["predicted"] == "HOME": agg["home"] = r["c"]
        agg["total"] = agg["away"] + agg["home"]

    return render(request, "events/participate.html", {
        "match": match, "history": history, "agg": agg, "now": now
    })

def _coupon_code(n=12):
    import string, secrets
    abc = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(abc) for _ in range(n))

@require_POST
def vote_api(request):
    """팝업에서 팀 선택 → 투표 저장 + 즉시 완료 메시지/쿠폰 안내"""
    result_id = request.POST.get("result_id")
    choice = request.POST.get("choice")  # 'AWAY' | 'HOME'
    if choice not in ("AWAY", "HOME"):
        return JsonResponse({"ok": False, "msg": "잘못된 선택"}, status=400)

    try:
        match = Result.objects.get(id=result_id)
    except Result.DoesNotExist:
        return JsonResponse({"ok": False, "msg": "경기를 찾을 수 없습니다."}, status=404)

    # 경기 시작 후에는 차단
    if match.date <= timezone.now():
        return JsonResponse({"ok": False, "msg": "경기가 시작되어 참여할 수 없습니다."}, status=409)

    token_id = _token_id(request)

    # 중복 참여 방지
    if Predict.objects.filter(token_id=token_id, result=match).exists():
        return JsonResponse({"ok": False, "msg": "이미 참여하셨습니다."}, status=409)

    pred = Predict.objects.create(
        token_id=token_id,
        predicted=choice,
        result=match,
    )

    # 즉시 지급용 ‘참여완료’ 쿠폰을 원하면(선택) 아래 주석 해제
    # code = _coupon_code()
    # Coupon.objects.create(token_id=token_id, code=code, status=0,
    #                       expire_at=timezone.now()+timezone.timedelta(days=7),
    #                       predict=pred)

    return JsonResponse({
        "ok": True,
        "msg": "이벤트 참여 완료!",
        # "coupon": {"code": code, "expire_at": ...}  # 즉시 발급 시 사용
    })

def rank_all_view(request):
    """
    종합/공격/수비 순위 한 페이지에 표시
    """
    total = TotalRank.objects.all().order_by('rank')
    attack = AttackRank.objects.all().order_by('rank')
    defend = DefendRank.objects.all().order_by('rank')

    return render(request, 'events/rank.html', {
        'total': total, 'attack': attack, 'defend': defend
    })