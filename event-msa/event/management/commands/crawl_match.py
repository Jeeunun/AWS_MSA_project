# event/management/commands/crawl_match.py
import requests
import pandas as pd
from itertools import zip_longest
from datetime import date, datetime, timedelta
from decimal import Decimal
from calendar import monthrange

from django.core.management.base import BaseCommand
from django.db import transaction

from ...models import Schedule 

# --- 요청 공통 설정 ---
REFERER = "https://sports.daum.net/schedule/kbo"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": REFERER,
    "Accept": "application/json, text/plain, */*",
}

# ---------- 유틸 ----------
def month_from_to(today: date | None = None):
    if today is None:
        today = date.today()
    y, m = today.year, today.month
    first = date(y, m, 1)
    last = date(y, m, monthrange(y, m)[1])
    return str(y), first.strftime("%Y%m%d"), last.strftime("%Y%m%d")

def hhmm(val):
    if val is None:
        return None
    s = str(val).zfill(4)
    return f"{s[:2]}:{s[2:4]}"

# ---------- 크롤링 ----------
def build_url(season: str, frm: str, to: str) -> str:
    return (
        "https://sports.daum.net/prx/hermes/api/game/schedule.json"
        f"?page=1&leagueCode=kbo&seasonKey={season}&fromDate={frm}&toDate={to}"
    )

def fetch_month_schedule(season: str, frm: str, to: str) -> dict:
    """
    한 달 범위 스케줄 JSON. 응답 구조는
      {"schedule": {"YYYYMMDD": [ {경기1}, ... ], ...}}
    """
    url = build_url(season, frm, to)
    sess = requests.Session()
    # 쿠키 확보(응답이 비는 경우가 있어 referer로 워밍업)
    _ = sess.get(REFERER, headers={"User-Agent": HEADERS["User-Agent"]}, timeout=15)
    r = sess.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    data = r.json()
    return data.get("schedule", {}) or {}

def schedule_to_dict(schedule_json: dict) -> dict[int, dict]:
    """
    날짜별 리스트를 정규화하여 dict[int_date] -> {컬럼: [값들]} 형태로 변환
    """
    start_dates = sorted(int(k) for k in schedule_json.keys())
    schedule = {
        d: {
            "startTime": [], "fieldName": [], "homeTeamName": [], "homeResult": [],
            "gameStatus": [], "awayTeamName": [], "awayResult": [], "winner": []
        }
        for d in start_dates
    }

    for date_str, matches in schedule_json.items():
        match_date = int(date_str)
        for game in (matches or []):
            schedule[match_date]["startTime"].append(hhmm(game.get("startTime")))
            schedule[match_date]["fieldName"].append(game.get("fieldName"))

            schedule[match_date]["homeTeamName"].append(game.get("homeTeamName"))
            schedule[match_date]["awayTeamName"].append(game.get("awayTeamName"))

            hr = game.get("homeResult")
            ar = game.get("awayResult")
            homeResult = int(hr) if hr is not None else None
            awayResult = int(ar) if ar is not None else None

            schedule[match_date]["homeResult"].append(homeResult)
            schedule[match_date]["awayResult"].append(awayResult)

            schedule[match_date]["gameStatus"].append(game.get("gameStatus"))

            if homeResult is not None and awayResult is not None:
                if homeResult > awayResult:
                    schedule[match_date]["winner"].append("home")
                elif homeResult < awayResult:
                    schedule[match_date]["winner"].append("away")
                else:
                    schedule[match_date]["winner"].append("draw")
            else:
                schedule[match_date]["winner"].append(None)

    return schedule

def schedule_to_df(schedule: dict) -> pd.DataFrame:
    """게임당 1행의 DataFrame으로 평탄화"""
    rows = []
    for match_date, bucket in schedule.items():
        for st, fld, hname, hres, status, aname, ares, win in zip_longest(
            bucket.get("startTime", []),
            bucket.get("fieldName", []),
            bucket.get("homeTeamName", []),
            bucket.get("homeResult", []),
            bucket.get("gameStatus", []),
            bucket.get("awayTeamName", []),
            bucket.get("awayResult", []),
            bucket.get("winner", []),
            fillvalue=None,
        ):
            rows.append({
                "date": match_date,           # int: YYYYMMDD
                "startTime": st,              # "HH:MM" or None
                "fieldName": fld,
                "homeTeamName": hname,
                "homeResult": hres,
                "awayTeamName": aname,
                "awayResult": ares,
                "gameStatus": status,
                "winner": win,
            })

    df = pd.DataFrame(rows)
    if not df.empty:
        # 날짜 -> date, 점수 -> nullable int
        df["match_date"] = pd.to_datetime(df["date"].astype(str), format="%Y%m%d", errors="coerce").dt.date
        for col in ("homeResult", "awayResult"):
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
        df = df.sort_values(["match_date", "startTime"], ascending=[True, True]).reset_index(drop=True)

        # 오늘 포함 이전 경기만 DB 업데이트 대상으로 제한
        # today = date.today()
        # df = df[df["match_date"] <= today]
    
    return df

# ---------- DB 저장 ----------
def _to_str(x):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    s = str(x).strip()
    return s if s != "" else None

def _to_int(x):
    if pd.isna(x):
        return None
    try:
        return int(x)
    except Exception:
        try:
            return int(Decimal(str(x)))
        except Exception:
            return None

@transaction.atomic
def upsert_results(df: pd.DataFrame):
    """
    df를 Schedule 테이블에 업데이트해서 저장
    """
    if df.empty:
        return 0, 0

    created_cnt = 0
    updated_cnt = 0

    for _, r in df.iterrows():
        # winner 값은 대문자로 정규화(예: HOME/AWAY/DRAW)
        winner = (str(r.get("winner")).upper()
                  if pd.notna(r.get("winner")) else None)

        lookup = dict(
            match_date=r["match_date"],
            startTime=_to_str(r.get("startTime")),
            awayTeamName=_to_str(r.get("awayTeamName")) or "",
            homeTeamName=_to_str(r.get("homeTeamName")) or "",
        )
        defaults = dict(
            awayResult=_to_int(r.get("awayResult")),
            homeResult=_to_int(r.get("homeResult")),
            gameStatus=_to_str(r.get("gameStatus")) or "",
            fieldname=_to_str(r.get("fieldName")),
            winner=winner,
        )
        obj, created = Schedule.objects.update_or_create(defaults=defaults, **lookup)
        if created:
            created_cnt+=1
        else:
            updated_cnt+=1
            
    return created_cnt, updated_cnt

# ---------- Django Command ----------
class Command(BaseCommand):
    help = "Daum KBO 월별 경기일정(결과/예정)을 크롤링하여 schedule 테이블에 누적하여 저장합니다."

    def add_arguments(self, parser):
        parser.add_argument("--year", type=int, default=None, help="시즌(기본: 오늘의 연도)")
        parser.add_argument("--from", dest="frm", type=str, default=None, help="시작일(YYYYMMDD, 기본: 이번달 1일)")
        parser.add_argument("--to", dest="to", type=str, default=None, help="종료일(YYYYMMDD, 기본: 이번달 말일)")

    def handle(self, *args, **opts):
        # 기간 계산
        season, default_from, default_to = month_from_to()
        season = str(opts["year"] or season)
        frm = opts["frm"] or default_from
        to = opts["to"] or default_to

        self.stdout.write(f"season={season} range={frm}~{to}")

        # 1) 크롤링
        schedule_json = fetch_month_schedule(season, frm, to)
        schedule = schedule_to_dict(schedule_json)

        # 2) DF 변환
        df = schedule_to_df(schedule)
        self.stdout.write(f"   - rows fetched: {len(df)}")

        # 3) DB 저장
        saved = upsert_results(df)
        self.stdout.write(self.style.SUCCESS(f"saved rows: {saved}"))
