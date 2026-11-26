# news/management/commands/crawl_news.py

from django.core.management.base import BaseCommand
from django.db import transaction, connection
from django.db.models import Q
from django.utils import timezone

from ...models import News

import requests, time
from urllib.parse import quote

# 동시 실행 방지 (MySQL GET_LOCK)
LOCK_KEY = "crawl_news_lock"
LOCK_TIMEOUT_SEC = 0   # 0: 이미 잡혀 있으면 바로 실패

def acquire_db_lock() -> bool:
    with connection.cursor() as cur:
        cur.execute("SELECT GET_LOCK(%s, %s)", [LOCK_KEY, LOCK_TIMEOUT_SEC])
        row = cur.fetchone()
    return bool(row and row[0] == 1)

def release_db_lock():
    try:
        with connection.cursor() as cur:
            cur.execute("DO RELEASE_LOCK(%s)", [LOCK_KEY])
    except Exception:
        pass

#Daum Sports API
BASE = "https://sports.daum.net/media-api/harmony/contents.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://sports.daum.net/baseball/news/breaking",
    "Origin": "https://sports.daum.net",
    "X-Requested-With": "XMLHttpRequest",
}
# 야구 카테고리(1028) — discoveryTag JSON을 두 번 인코딩(브라우저와 동일)
DISCOVERY_JSON = '{"group":"media","key":"defaultCategoryId3","value":"1028"}'
DISCOVERY_ENC2 = quote(quote(DISCOVERY_JSON, safe=""), safe="")  # %257B...%257D

def _get_items(d: dict):
    return d.get("result", {}).get("contents") or d.get("contents") or []

def _parse_keywords(raw_kw):
    if isinstance(raw_kw, list):
        buf = []
        for k in raw_kw:
            if isinstance(k, str):
                s = k.strip()
                if s: buf.append(s)
            elif isinstance(k, dict):
                s = str(k.get("name", "")).strip()
                if s: buf.append(s)
        return ",".join(buf)
    return (str(raw_kw or "")).strip()

def _fetch_page(ymd: str, page: int, size: int):
    createDt = f"{ymd}000000~{ymd}235959"
    url = (
        f"{BASE}?page={page}&consumerType=HARMONY&status=SERVICE"
        f"&createDt={createDt}&discoveryTag%5B0%5D={DISCOVERY_ENC2}&size={size}"
    )
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return _get_items(r.json())

class Command(BaseCommand):
    help = "Daum 스포츠(야구) 오늘 기사 수집 → DB 저장 (동시 실행 방지 적용)"

    SIZE = 50          # 페이지당 아이템 수
    SLEEP_SEC = 0.12   # API 호출 간 간격
    MAX_PAGES = 500    # 안전 상한

    def handle(self, *args, **kwargs):
        if not acquire_db_lock():
            self.stdout.write(self.style.WARNING("[SKIP] another crawl is in progress"))
            return
        try:
            self._run()
        finally:
            release_db_lock()

    def _run(self):
        today = timezone.localdate()
        ymd = today.strftime("%Y%m%d")
        self.stdout.write(self.style.NOTICE(f"[INFO] target date(KST): {ymd}"))

        # (선택) 전일/NULL 데이터 정리
        deleted_count, _ = News.objects.filter(
            Q(crawl_date__lt=today) | Q(crawl_date__isnull=True)
        ).delete()
        self.stdout.write(self.style.NOTICE(f"[CLEANUP] removed old rows: {deleted_count}"))

        # 오늘 이미 저장된 링크(중복 감소)
        existing_links = set(
            News.objects.filter(crawl_date=today).values_list("link", flat=True)
        )
        seen_links = set(existing_links)
        rows = []
        seen_sigs = set()
        page = 0

        for _ in range(self.MAX_PAGES):
            try:
                items = _fetch_page(ymd, page, self.SIZE)
            except requests.RequestException as e:
                self.stdout.write(self.style.ERROR(f"[ERROR] request failed: {e}"))
                break

            self.stdout.write(self.style.NOTICE(f"[PAGE {page}] items={len(items)}"))
            if not items:
                self.stdout.write(self.style.NOTICE("→ empty page. stop"))
                break

            sig = (items[0].get("title",""), items[-1].get("title",""))
            if sig in seen_sigs:
                self.stdout.write(self.style.WARNING("→ repeated page signature. stop"))
                break
            seen_sigs.add(sig)

            added = 0
            for it in items:
                title = (it.get("title") or "").strip()
                link = (
                    it.get("contentUrl")
                    or it.get("cpLink")
                    or it.get("cpLinkUrl")
                    or it.get("url")
                    or ""
                ).strip()
                if not title or not link:
                    continue
                if link in seen_links:
                    continue

                kw = _parse_keywords(it.get("keywords"))
                rows.append(News(title=title, keyword=kw or None, link=link, crawl_date=today))
                seen_links.add(link)
                added += 1

            if added == 0:
                self.stdout.write(self.style.WARNING("→ no new rows added this page. stop"))
                break
            if len(items) < self.SIZE:
                self.stdout.write(self.style.NOTICE("→ last batch (items < size). stop"))
                break

            page += 1
            time.sleep(self.SLEEP_SEC)

        created_count, _ = self._bulk_insert_ignore(rows)
        self.stdout.write(self.style.SUCCESS(
            f"[DONE] scraped={len(seen_links) - len(existing_links)} created={created_count}"
        ))

    def _bulk_insert_ignore(self, objs):
        if not objs:
            return 0, 0
        # 실행 내 중복 제거(메모리)
        by_link = {o.link: o for o in objs}
        objs = list(by_link.values())
        with transaction.atomic():
            News.objects.bulk_create(objs, ignore_conflicts=True)
        return len(objs), 0

