# kbo/management/commands/fetch_kbo_simple.py
import time
import shutil
import re
from typing import List, Dict, Optional, Any
from django.core.management.base import BaseCommand
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import requests
from kbo.models import Team, Manager, Player
from datetime import datetime

TEAM_PREFIX_TO_CODE = {
    'LG': 'LG', '두산': 'DS', 'SSG': 'SSG', '롯데': 'LT', 'KIA': 'KIA', '삼성': 'SS', '한화': 'HH', 'NC': 'NC', '키움': 'WO', 'KT': 'KT'
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
}

# Fixed Daum team IDs based on provided URLs
DAUM_TEAM_ID_MAP: Dict[str, int] = {
    'KIA': 389,      # kia (KIA)
    'LG': 387,       # lg (LG)
    'SSG': 384,      # ssg (SSG)
    'LT': 386,       # lotte (롯데)
    'WO': 382,       # kiwoom (키움)
    'KT': 394601,    # kt (KT)
    'NC': 172615,    # nc (NC)
    'DS': 385,       # doosan (두산)
    'SS': 383,       # samsung (삼성)
    'HH': 390,       # hanwha (한화)
}

# KBO 팀 정보
TEAM_DATA = [
    ('KIA', 'KIA 타이거즈'),
    ('LG', 'LG 트윈스'),
    ('SSG', 'SSG 랜더스'),
    ('LT', '롯데 자이언츠'),
    ('WO', '키움 히어로즈'),
    ('KT', 'KT 위즈'),
    ('NC', 'NC 다이노스'),
    ('DS', '두산 베어스'),
    ('SS', '삼성 라이온즈'),
    ('HH', '한화 이글스')
]

def build_driver() -> webdriver.Chrome:
    """Chrome WebDriver를 생성합니다"""
    try:
        options = Options()
        
        # Chrome 옵션 설정
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--lang=ko-KR,ko')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-features=Translate,AutomationControlled')
        options.add_argument('--excludeSwitches=enable-automation')
        options.add_argument('--disable-infobars')
        options.add_argument(f'--user-agent={HEADERS["User-Agent"]}')
        
        try:
            # Selenium 4.x에서는 Service 객체를 사용하는 것이 권장됨
            service = Service()
            driver = webdriver.Chrome(options=options, service=service)
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            
        except WebDriverException as e:
            # fallback to old method
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
        
        return driver
        
    except Exception as e:
        raise e

def parse_manager_name_from_team_info_html(html: str) -> str:
    """HTML에서 감독 이름을 추출합니다"""
    soup = BeautifulSoup(html, 'html.parser')
    label = soup.find(lambda t: t.name in ['th', 'dt', 'span', 'strong'] and t.get_text(strip=True) == '감독')
    if label:
        nxt = label.find_next(['td', 'dd', 'span', 'a', 'em'])
        if nxt:
            return nxt.get_text(strip=True)
    blk = soup.find(lambda t: t.name in ['li', 'div', 'p'] and '감독' in t.get_text())
    if blk:
        txt = blk.get_text(' ', strip=True)
        for token in txt.split():
            if '감독' not in token and len(token) >= 2:
                return token
    return ''

def parse_players_from_daum_html_v2(html: str) -> List[Dict]:
    """Daum HTML에서 선수 정보 추출 (v2 방식)"""
    soup = BeautifulSoup(html, 'html.parser')
    players = []
    
    # 선수 테이블 찾기
    table = soup.find('table', class_='tbl_teamplayer')
    if not table:
        return players
    
    # 테이블 행들 파싱
    for tr in table.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) >= 3:
            try:
                back_number = tds[0].get_text(strip=True)
                name = tds[1].get_text(strip=True)
                position = tds[2].get_text(strip=True)
                
                # 추가 정보가 있는 경우
                height = ''
                weight = ''
                birthdate = ''
                bats_throws = ''
                
                if len(tds) > 3:
                    height = tds[3].get_text(strip=True) if tds[3] else ''
                if len(tds) > 4:
                    weight = tds[4].get_text(strip=True) if tds[4] else ''
                if len(tds) > 5:
                    birthdate = tds[5].get_text(strip=True) if tds[5] else ''
                if len(tds) > 6:
                    bats_throws = tds[6].get_text(strip=True) if tds[6] else ''
                
                if name and name != '이름':  # 헤더 행 제외
                    players.append({
                        'name': name,
                        'back_number': back_number,
                        'position': position,
                        'height': height,
                        'weight': weight,
                        'birthdate': birthdate,
                        'bats_throws': bats_throws,
                        'bats': '',
                        'throws': ''
                    })
            except Exception as e:
                continue
    
    return players

def adapt_players_v2_to_rows(players: List[dict]) -> List[dict]:
    """v2 선수 데이터를 기존 형식으로 변환"""
    if not players:
        return []
    
    rows = []
    for player in players:
        # 생년월일 파싱
        birthdate = None
        if player.get('birthdate'):
            try:
                # 다양한 날짜 형식 처리
                date_str = player['birthdate']
                if '-' in date_str:
                    birthdate = datetime.strptime(date_str, '%Y-%m-%d').date()
                elif '.' in date_str:
                    birthdate = datetime.strptime(date_str, '%Y.%m.%d').date()
                elif '/' in date_str:
                    birthdate = datetime.strptime(date_str, '%Y/%m/%d').date()
            except:
                birthdate = None
        
        # 투타 정보 파싱
        bats_throws = player.get('bats_throws', '')
        bats = ''
        throws = ''
        
        if bats_throws:
            if '우투' in bats_throws:
                throws = '우투'
            elif '좌투' in bats_throws:
                throws = '좌투'
            
            if '우타' in bats_throws:
                bats = '우타'
            elif '좌타' in bats_throws:
                bats = '좌타'
            elif '양타' in bats_throws:
                bats = '양타'
        
        rows.append({
            'name': player['name'],
            'back_number': player['back_number'],
            'position': player['position'],
            'height': player['height'],
            'weight': player['weight'],
            'birthdate': birthdate,
            'bats_throws': bats_throws,
            'bats': bats,
            'throws': throws
        })
    
    return rows

def get_html_via_requests(url: str) -> str:
    """requests를 사용하여 HTML을 가져옵니다"""
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text

def extract_stadium_from_html(html: str) -> str:
    """HTML에서 구장 정보를 추출합니다"""
    soup = BeautifulSoup(html, 'html.parser')
    # Look for labels like '구장', '홈구장'
    label = soup.find(lambda t: t.name in ['span','strong','dt','th'] and t.get_text(strip=True) in ['구장','홈구장'])
    if label:
        nxt = label.find_next(['span','dd','td','em','a'])
        if nxt:
            return nxt.get_text(strip=True)
    # Fallback: text block containing '구장'
    blk = soup.find(lambda t: t.name in ['div','p','li'] and '구장' in t.get_text())
    if blk:
        txt = blk.get_text(' ', strip=True)
        parts = txt.split()
        # choose last token that is not label-like
        for i in range(len(parts)-1, -1, -1):
            if '구장' not in parts[i]:
                return parts[i]
    return ''

def fetch_team_data_from_daum(team_code: str, driver: webdriver.Chrome = None) -> dict:
    """Daum 스포츠에서 팀 데이터를 가져옵니다 (fetch_kbo2.py 방식)"""
    try:
        daum_id = DAUM_TEAM_ID_MAP.get(team_code)
        if not daum_id:
            return {'team_name': f"{team_code} 팀", 'players': []}
        
        daum_url = f'https://sports.daum.net/team/kbo/{daum_id}/squad'
        
        if driver:
            # Selenium 방식
            try:
                driver.get(daum_url)
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'table')))
                rendered = driver.page_source
                
                # 우선 탭 토글을 순회하여 모든 포지션 수집 시도
                collected: List[dict] = []
                positions = ['P', 'IF', 'C', 'OF']
                for pos_key in positions:
                    try:
                        toggle = driver.find_element(By.CSS_SELECTOR, f'.group_toggle .toggle_input[data-position="{pos_key}"]')
                        toggle.click()
                        time.sleep(0.8)
                        rendered_pos = driver.page_source
                        players_v2 = parse_players_from_daum_html_v2(rendered_pos)
                        rows_pos = adapt_players_v2_to_rows(players_v2)
                        if rows_pos:
                            collected.extend(rows_pos)
                            print(f"  📍 {pos_key} 포지션에서 {len(rows_pos)}명 선수 발견")
                        else:
                            print(f"  ⚠️ {pos_key} 포지션에서 선수 발견 안됨")
                    except Exception as e:
                        # 탭 요소가 없거나 클릭 실패 → 다음 포지션으로 진행
                        print(f"  ❌ {pos_key} 포지션 토글 실패: {str(e)}")
                        continue
                
                # 토글 결과가 있으면 사용, 없으면 현재 화면에서 파싱
                if collected:
                    players = collected
                    print(f"  ✅ 토글 방식으로 총 {len(collected)}명 선수 수집")
                else:
                    players_v2 = parse_players_from_daum_html_v2(rendered)
                    players = adapt_players_v2_to_rows(players_v2)
                    print(f"  🔍 현재 화면에서 {len(players)}명 선수 파싱")
                
            except Exception as e:
                print(f"  ❌ Selenium 크롤링 오류: {str(e)}")
                players = []
        else:
            # requests 방식
            try:
                daum_html = get_html_via_requests(daum_url)
                players_v2 = parse_players_from_daum_html_v2(daum_html)
                players = adapt_players_v2_to_rows(players_v2)
                print(f"  🌐 requests 방식으로 {len(players)}명 선수 파싱")
            except Exception as e:
                print(f"  ❌ requests 크롤링 오류: {str(e)}")
                players = []
        
        # 중복 제거
        unique_players = []
        seen_names = set()
        for player in players:
            if player['name'] not in seen_names:
                unique_players.append(player)
                seen_names.add(player['name'])
        
        # 디버깅 정보 출력
        print(f"팀 {team_code} - 수집된 선수 수: {len(players)}명")
        print(f"팀 {team_code} - 중복 제거 후: {len(unique_players)}명")
        if unique_players:
            print(f"팀 {team_code} - 선수 목록: {[p['name'] for p in unique_players[:10]]}")
        
        return {
            'team_name': f"{team_code} 팀",
            'players': unique_players
        }
        
    except Exception as e:
        print(f"Daum에서 팀 {team_code} 데이터 가져오기 실패: {e}")
        return {'team_name': f"{team_code} 팀", 'players': []}



class Command(BaseCommand):
    help = 'KBO 팀/감독/선수 최신 데이터 수집 (Daum 사이트만 사용, fetch_kbo2.py 방식)'

    def add_arguments(self, parser):
        parser.add_argument('--only', type=str, help='특정 팀 코드만(e.g., LG,OB,SSG,...)')
        parser.add_argument('--sleep', type=float, default=0.5, help='요청 간 대기(초)')
        parser.add_argument('--no-browser', action='store_true', help='브라우저 없이 requests로만 수집')

    def handle(self, *args, **opts):
        only = opts.get('only')
        pause = float(opts.get('sleep') or 0.5)
        no_browser = bool(opts.get('no-browser'))

        self.stdout.write(f"=== KBO 데이터 수집 시작 ===")
        self.stdout.write(f"브라우저 사용: {'비활성화' if no_browser else '활성화'}")
        self.stdout.write(f"대기 시간: {pause}초")
        
        if only:
            # 단일 팀 크롤링
            self.crawl_single_team(only, pause, no_browser)
        else:
            # 전체 팀 크롤링
            self.crawl_all_teams(pause, no_browser)
        
        self.stdout.write(f"=== KBO 데이터 수집 완료 ===")

    def crawl_single_team(self, team_code: str, pause: float, no_browser: bool):
        """단일 팀 크롤링"""
        # 해당 팀 찾기
        target_team = None
        for code, name in TEAM_DATA:
            if code == team_code:
                target_team = (code, name)
                break
        
        if not target_team:
            self.stdout.write(self.style.ERROR(f'팀 코드 {team_code}를 찾을 수 없습니다.'))
            return
        
        self.crawl_team(target_team[0], target_team[1], pause, no_browser)

    def crawl_all_teams(self, pause: float, no_browser: bool):
        """전체 팀 크롤링"""
        for code, team_name in TEAM_DATA:
            self.crawl_team(code, team_name, pause, no_browser)
            time.sleep(pause)

    def crawl_team(self, code: str, team_name: str, pause: float, no_browser: bool):
        """개별 팀 크롤링 (fetch_kbo2.py 방식)"""
        self.stdout.write(f"\n=== {team_name} ({code}) 크롤링 시작 ===")
        
        driver = None
        if not no_browser:
            try:
                self.stdout.write(f"  🔧 Chrome WebDriver 생성 중...")
                driver = build_driver()
                self.stdout.write(f"  ✅ Chrome WebDriver 생성 완료")
            except Exception as e:
                self.stdout.write(f"  ❌ Chrome WebDriver 생성 실패: {e}")
                self.stdout.write(f"  🔄 requests 모드로 자동 전환")
                driver = None
                no_browser = True
        
        try:
            # 기존 팀이 있는지 확인 (이름 또는 코드로)
            existing_team = None
            try:
                existing_team = Team.objects.get(code=code)
            except Team.DoesNotExist:
                try:
                    existing_team = Team.objects.get(name=team_name)
                except Team.DoesNotExist:
                    pass
            
            if existing_team:
                # 기존 팀이 있으면 코드와 이름을 모두 업데이트
                existing_team.code = code
                existing_team.name = team_name
                existing_team.save()
                team = existing_team
                self.stdout.write(f"  ✅ 기존 팀 업데이트: {team.name}")
            else:
                # 새 팀 생성
                team = Team.objects.create(code=code, name=team_name)
                self.stdout.write(f"  ✅ 새 팀 생성: {team.name}")

            mgr_name: Optional[str] = ''
            rows: List[dict] = []
            daum_id = DAUM_TEAM_ID_MAP.get(code)
            
            if daum_id:
                daum_url = f'https://sports.daum.net/team/kbo/{daum_id}/squad'
                try:
                    if driver and not no_browser:
                        # Selenium 방식
                        self.stdout.write(f"  🌐 Selenium으로 페이지 로딩 중: {daum_url}")
                        driver.get(daum_url)
                        
                        # 페이지 로딩 대기
                        try:
                            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'table')))
                            self.stdout.write(f"  ✅ 페이지 로딩 완료")
                        except TimeoutException:
                            self.stdout.write(f"  ⚠️ 테이블 로딩 타임아웃, 현재 상태로 진행")
                        
                        rendered = driver.page_source
                        
                        # 디버깅: HTML 구조 확인
                        self.stdout.write(f"  🔍 페이지 URL: {daum_url}")
                        self.stdout.write(f"  📄 HTML 길이: {len(rendered)} 문자")
                        
                        # HTML 소스 저장 (디버깅용)
                        debug_file = f"debug_{team.code}_page.html"
                        with open(debug_file, 'w', encoding='utf-8') as f:
                            f.write(rendered)
                        self.stdout.write(f"  💾 HTML 소스 저장: {debug_file}")
                        
                        # 선수 테이블 존재 여부 확인
                        soup = BeautifulSoup(rendered, 'html.parser')
                        tables = soup.find_all('table')
                        self.stdout.write(f"  📊 페이지 내 테이블 수: {len(tables)}")
                        
                        for i, table in enumerate(tables):
                            table_class = table.get('class', [])
                            table_id = table.get('id', '')
                            self.stdout.write(f"    테이블 {i+1}: class={table_class}, id={table_id}")
                        
                        # 선수 테이블 특별 확인
                        player_table = soup.find('table', class_='tbl_teamplayer')
                        if player_table:
                            self.stdout.write(f"  ✅ 선수 테이블 발견: tbl_teamplayer")
                            rows_table = player_table.find_all('tr')
                            self.stdout.write(f"    테이블 행 수: {len(rows_table)}")
                            if rows_table:
                                # 첫 번째 행(헤더) 확인
                                header_cells = rows_table[0].find_all(['th', 'td'])
                                header_texts = [cell.get_text(strip=True) for cell in header_cells]
                                self.stdout.write(f"    헤더: {header_texts}")
                        else:
                            self.stdout.write(f"  ❌ 선수 테이블(tbl_teamplayer) 발견 안됨")
                            
                            # 대안 테이블 찾기
                            alt_tables = soup.find_all('table')
                            for i, table in enumerate(alt_tables):
                                if table.find('tr') and table.find('td'):
                                    sample_text = table.get_text()[:100]
                                    self.stdout.write(f"    대안 테이블 {i+1}: {sample_text}...")
                        
                        # 감독 정보 추출
                        tmp_mgr = parse_manager_name_from_team_info_html(rendered)
                        if tmp_mgr:
                            mgr_name = tmp_mgr
                        
                        # 구장 정보 추출
                        stadium = extract_stadium_from_html(rendered) or team.stadium
                        if stadium and stadium != team.stadium:
                            Team.objects.filter(pk=team.pk).update(stadium=stadium)

                        # 우선 탭 토글을 순회하여 모든 포지션 수집 시도
                        collected: List[dict] = []
                        positions = ['P', 'IF', 'C', 'OF']
                        for pos_key in positions:
                            try:
                                toggle = driver.find_element(By.CSS_SELECTOR, f'.group_toggle .toggle_input[data-position="{pos_key}"]')
                                toggle.click()
                                time.sleep(0.8)
                                rendered_pos = driver.page_source
                                players_v2 = parse_players_from_daum_html_v2(rendered_pos)
                                rows_pos = adapt_players_v2_to_rows(players_v2)
                                if rows_pos:
                                    collected.extend(rows_pos)
                                    self.stdout.write(f"  📍 {pos_key} 포지션에서 {len(rows_pos)}명 선수 발견")
                                else:
                                    self.stdout.write(f"  ⚠️ {pos_key} 포지션에서 선수 발견 안됨")
                            except Exception as e:
                                # 탭 요소가 없거나 클릭 실패 → 다음 포지션으로 진행
                                self.stdout.write(f"  ❌ {pos_key} 포지션 토글 실패: {str(e)}")
                                continue
                        
                        # 토글 결과가 있으면 사용, 없으면 현재 화면에서 파싱
                        if collected:
                            rows = collected
                            self.stdout.write(f"  ✅ 토글 방식으로 총 {len(collected)}명 선수 수집")
                        else:
                            players_v2 = parse_players_from_daum_html_v2(rendered)
                            rows = adapt_players_v2_to_rows(players_v2)
                            self.stdout.write(f"  🔍 현재 화면에서 {len(rows)}명 선수 파싱")
                    else:
                        # requests 방식
                        self.stdout.write(f"  🌐 requests로 페이지 로딩 중: {daum_url}")
                        daum_html = get_html_via_requests(daum_url)
                        self.stdout.write(f"  ✅ requests 페이지 로딩 완료")
                        
                        tmp_mgr = parse_manager_name_from_team_info_html(daum_html)
                        if tmp_mgr:
                            mgr_name = tmp_mgr
                        stadium = extract_stadium_from_html(daum_html) or team.stadium
                        if stadium and stadium != team.stadium:
                            Team.objects.filter(pk=team.pk).update(stadium=stadium)
                        players_v2 = parse_players_from_daum_html_v2(daum_html)
                        rows = adapt_players_v2_to_rows(players_v2)
                        self.stdout.write(f"  🌐 requests 방식으로 {len(rows)}명 선수 파싱")
                except Exception as e:
                    self.stdout.write(f"  ❌ 크롤링 오류: {str(e)}")
                    import traceback
                    self.stdout.write(f"  📝 상세 오류: {traceback.format_exc()}")
                    pass

            if not mgr_name or not rows:
                self.stdout.write(self.style.WARNING(f'{team.name} - 데이터 추출 실패 (Daum에서만 시도)'))

            if mgr_name:
                Manager.objects.update_or_create(team=team, defaults={'name': mgr_name})

            Player.objects.filter(team=team).delete()
            objs = [Player(team=team, **row) for row in rows]
            if objs:
                Player.objects.bulk_create(objs, batch_size=300)

            manager_name_to_log = (mgr_name or Manager.objects.filter(team=team).values_list('name', flat=True).first() or '-')
            self.stdout.write(self.style.SUCCESS(f'{team.name} ✔ (감독:{manager_name_to_log}, 선수:{len(objs)})'))
            
        finally:
            # 각 팀 크롤링 완료 후 드라이버 정리
            if driver:
                try:
                    driver.quit()
                    self.stdout.write(f"  🧹 {team_name} Chrome 드라이버 정리 완료")
                except:
                    pass
