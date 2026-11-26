# event/management/commands/crawl_match.py
from datetime import datetime, date
from collections import defaultdict
import re, time, os

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from ...models import Result


class Command(BaseCommand):
    help = "KBO 월별 일정 적재 + 일자 결과 업데이트 (schedule/update/both)"

    def add_arguments(self, parser):
        parser.add_argument("--mode", choices=["schedule", "update", "both"], default="schedule")
        parser.add_argument("--year", type=int, default=date.today().year)
        parser.add_argument("--month", type=int, default=date.today().month)
        parser.add_argument("--date", help="YYYY-MM-DD (mode=update/both에서 갱신할 날짜, 기본=오늘)")

    def handle(self, *args, **opt):
        mode  = opt.get("mode", "schedule")
        year  = opt.get("year", date.today().year)
        month = opt.get("month", date.today().month)
        day   = opt.get("date") or date.today().strftime("%Y-%m-%d")

        driver = webdriver.Chrome()
        url = "https://sports.daum.net/schedule/kbo"

        try:
            # 월별 전체 일정부터 확보
            schedule_by_date = self.result_crawling(driver, url, year, month)

            if mode in ("schedule", "both"):
                self.ingest_month(schedule_by_date, year, month)
                self.stdout.write(self.style.SUCCESS(f"[schedule] {year}-{month:02d} 적재 완료"))

            if mode in ("update", "both"):
                self.update_day(schedule_by_date, day)
                self.stdout.write(self.style.SUCCESS(f"[update] {day} 결과 갱신 완료"))

        finally:
            driver.quit()

        self.stdout.write(self.style.SUCCESS("완료"))

    # ---------------------- 파싱 유틸 ----------------------
    @staticmethod
    def parse_game_line(line: str):
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 6:
            return None
        head = parts[0]
        hh = head.split()
        game_time = hh[0] if hh else ""
        stadium = " ".join(hh[1:]) if len(hh) > 1 else ""

        status = parts[1]
        away_team = parts[2]
        at_score_raw = parts[3]
        home_team = parts[4]
        ht_score_raw = parts[5]

        def to_score(s):
            s = (s or "").strip()
            return None if s in ("", "-") else int(s)

        return {
            "start_time": game_time,
            "stadium": stadium,
            "status": status,
            "away_team": away_team,
            "at_score": to_score(at_score_raw),
            "home_team": home_team,
            "ht_score": to_score(ht_score_raw),
        }

    @staticmethod
    def pick_winner(at, ht, away, home):
        if at is None or ht is None: return ""
        if at > ht: return away
        if ht > at: return home
        return ""

    # ---------------------- DB 적재/갱신 ----------------------
    @transaction.atomic
    def ingest_month(self, schedule_by_date: dict, year: int, month: int):
        for k, lines in schedule_by_date.items():  # k 예: '08.11 월'
            mm, dd = k.split()[0].split(".")
            yyyy_mm_dd = f"{year}-{mm}-{dd}"
            for line in lines:
                if "경기가 없습니다" in line: 
                    continue
                g = self.parse_game_line(line)
                if not g: 
                    continue

                obj, created = Result.objects.get_or_create(
                    date=datetime.strptime(yyyy_mm_dd + " " + (g["start_time"] or "00:00"), "%Y-%m-%d %H:%M"),
                    away_team=g["away_team"],
                    home_team=g["home_team"],
                    start_time=g["start_time"] or None,
                    defaults={
                        "status": g["status"] or "scheduled",
                        "stadium": g["stadium"] or "",
                        "at_score": g["at_score"],
                        "ht_score": g["ht_score"],
                        "winner": self.pick_winner(g["at_score"], g["ht_score"], g["away_team"], g["home_team"]),
                    },
                )
                if not created:
                    changed = False
                    for f, v in [
                        ("status", g["status"] or obj.status),
                        ("stadium", g["stadium"] or obj.stadium),
                        ("at_score", g["at_score"]),
                        ("ht_score", g["ht_score"]),
                        ("start_time", g["start_time"] or obj.start_time),
                    ]:
                        if getattr(obj, f) != v:
                            setattr(obj, f, v); changed = True
                    nw = self.pick_winner(g["at_score"], g["ht_score"], g["away_team"], g["home_team"])
                    if obj.winner != nw: obj.winner = nw; changed = True
                    if changed:
                        obj.save(update_fields=["status","stadium","at_score","ht_score","start_time","winner","updated_at"])

    @transaction.atomic
    def update_day(self, schedule_by_date: dict, yyyy_mm_dd: str):
        key_for_day = datetime.strptime(yyyy_mm_dd, "%Y-%m-%d").strftime("%m.%d")
        target_key = next((k for k in schedule_by_date.keys() if k.startswith(key_for_day)), None)
        if not target_key:
            self.stderr.write(f"{yyyy_mm_dd} 데이터 없음"); 
            return

        for line in schedule_by_date[target_key]:
            if "경기가 없습니다" in line: 
                continue
            g = self.parse_game_line(line)
            if not g: 
                continue

            game_dt = datetime.strptime(yyyy_mm_dd + " " + (g["start_time"] or "00:00"), "%Y-%m-%d %H:%M")
            qs = Result.objects.filter(date=game_dt, away_team=g["away_team"], home_team=g["home_team"])
            if not qs.exists():
                Result.objects.create(
                    date=game_dt,
                    start_time=g["start_time"] or None,
                    away_team=g["away_team"],
                    home_team=g["home_team"],
                    status=g["status"] or "scheduled",
                    stadium=g["stadium"] or "",
                    at_score=g["at_score"],
                    ht_score=g["ht_score"],
                    winner=self.pick_winner(g["at_score"], g["ht_score"], g["away_team"], g["home_team"]),
                )
                continue

            obj = qs.first()
            changed = False
            for f, v in [("status", g["status"] or obj.status),
                         ("stadium", g["stadium"] or obj.stadium),
                         ("at_score", g["at_score"]),
                         ("ht_score", g["ht_score"])]:
                if getattr(obj, f) != v:
                    setattr(obj, f, v); changed = True
            nw = self.pick_winner(g["at_score"], g["ht_score"], g["away_team"], g["home_team"])
            if obj.winner != nw: obj.winner = nw; changed = True
            if changed:
                obj.save(update_fields=["status","stadium","at_score","ht_score","winner","updated_at"])

    # ---------------------- 크롤링 ----------------------
    def result_crawling(self, driver, url, year, month):
        wait = WebDriverWait(driver, 12)
        driver.get(url)
        self.try_close_any_popup(driver)

        # 캘린더 열기 → 연/월 선택
        self.pick_year_month(driver, year, month, wait)

        # 스크롤
        self.scroll_down(driver, max_scroll=8)

        # 텍스트 파싱
        schedule_by_date = defaultdict(list)
        date_pattern = re.compile(r"^\d{2}\.\d{2}")

        blocks = wait.until(EC.presence_of_all_elements_located((By.ID, "scheduleList")))
        for blk in blocks:
            lines = blk.text.strip().split("\n")
            current_date, current_game, is_game_block = None, [], False

            for line in lines:
                if date_pattern.match(line):    # '08.11 월'
                    if current_game:
                        schedule_by_date[current_date].append(", ".join(current_game))
                        current_game = []
                    current_date = " ".join(line.split()[:2])
                    if "경기가 없습니다" in line:
                        schedule_by_date[current_date].append("경기가 없습니다.")
                        current_date, is_game_block = None, False
                    else:
                        is_game_block = True
                        current_game.append(" ".join(line.split()[2:]))
                elif is_game_block:
                    if re.match(r"^\d{2}:\d{2}", line) and current_game:
                        schedule_by_date[current_date].append(", ".join(current_game))
                        current_game = [line]
                    else:
                        current_game.append(line)

            if current_game and current_date:
                schedule_by_date[current_date].append(", ".join(current_game))

        return schedule_by_date

    def pick_year_month(self, driver, year, month, wait):
        # 캘린더 버튼
        cal_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn_calendar, .link_calendar")))
        driver.execute_script("arguments[0].click()", cal_btn)
        time.sleep(0.2)

        # 연도 드롭다운 열기
        year_toggle = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".choice_calendar.choice_year > a, .choice_calendar.choice_year .btn_select")))
        driver.execute_script("arguments[0].click()", year_toggle)

        # 연도 선택 (대체 셀렉터/XPath 시도)
        try:
            year_item = WebDriverWait(driver, 6).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, f".choice_calendar.choice_year .list_calendar a[data-year='{year}']"))
            )
        except TimeoutException:
            year_item = WebDriverWait(driver, 6).until(
                EC.element_to_be_clickable((By.XPATH, f"//a[@data-year='{year}' or normalize-space()='{year}']"))
            )
        driver.execute_script("arguments[0].click()", year_item)
        time.sleep(0.2)

        # 월 드롭다운 열기
        month_toggle = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".choice_calendar.choice_month > a, .choice_calendar.choice_month .btn_select")))
        driver.execute_script("arguments[0].click()", month_toggle)

        # 월 선택
        month_str = f"{int(month):02d}"
        try:
            month_item = WebDriverWait(driver, 6).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, f".choice_calendar.choice_month .list_calendar a[data-month='{month_str}']"))
            )
        except TimeoutException:
            month_item = WebDriverWait(driver, 6).until(
                EC.element_to_be_clickable((By.XPATH, f"//a[@data-month='{month_str}']"))
            )
        driver.execute_script("arguments[0].click()", month_item)
        time.sleep(0.3)

    def try_close_any_popup(self, driver):
        for sel in [".btn_close", ".btn_confirm", "button[aria-label='닫기']", ".ico_close", ".layer_close"]:
            try:
                for b in driver.find_elements(By.CSS_SELECTOR, sel)[:3]:
                    try: driver.execute_script("arguments[0].click()", b)
                    except Exception: pass
            except Exception:
                pass

    def scroll_down(self, driver, max_scroll=6):
        last_h = driver.execute_script("return document.body.scrollHeight")
        for _ in range(max_scroll):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.2)
            new_h = driver.execute_script("return document.body.scrollHeight")
            if new_h == last_h: break
            last_h = new_h
