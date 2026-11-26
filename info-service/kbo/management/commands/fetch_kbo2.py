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


def clean_numeric_value(value: str, field_type: str = 'int') -> Any:
    """숫자 데이터 정제 함수"""
    if not value or value == '':
        return 0 if field_type == 'int' else 0.0
    
    # 문자열에서 숫자만 추출
    cleaned = re.sub(r'[^\d.]', '', str(value))
    
    if not cleaned:
        return 0 if field_type == 'int' else 0.0
    
    try:
        if field_type == 'int':
            return int(cleaned)
        elif field_type == 'float':
            return float(cleaned)
        else:
            return cleaned
    except (ValueError, TypeError):
        return 0 if field_type == 'int' else 0.0

def clean_height_cm(height_str: str) -> str:
    """키 데이터 정제 함수"""
    if not height_str or height_str == '':
        return ''
    
    # 숫자만 추출
    cleaned = re.sub(r'[^\d]', '', str(height_str))
    if cleaned:
        return f"{cleaned}cm"
    return ''

def clean_weight_kg(weight_str: str) -> str:
    """몸무게 데이터 정제 함수"""
    if not weight_str or weight_str == '':
        return ''
    
    # kg, g 등 단위 제거 후 숫자만 추출 (소수점 포함)
    weight_str = str(weight_str).lower()
    
    # kg 단위 처리
    if 'kg' in weight_str:
        cleaned = re.sub(r'[^\d.]', '', weight_str)
        if cleaned:
            return f"{cleaned}kg"
    # g 단위 처리 (1000g = 1kg)
    elif 'g' in weight_str:
        cleaned = re.sub(r'[^\d.]', '', weight_str)
        if cleaned:
            try:
                g_value = float(cleaned)
                kg_value = g_value / 1000.0
                return f"{kg_value}kg"
            except (ValueError, TypeError):
                return ''
    else:
        # 단위가 없는 경우
        cleaned = re.sub(r'[^\d.]', '', weight_str)
        if cleaned:
            return f"{cleaned}kg"
    
    return ''

def clean_birth_date(birth_str: str) -> Optional[str]:
    """생년월일 데이터 정제 함수"""
    if not birth_str or birth_str == '':
        return None
    
    # YYYY-MM-DD 형식으로 변환 시도
    try:
        # 다양한 날짜 형식 처리
        if re.match(r'\d{4}-\d{2}-\d{2}', birth_str):
            return birth_str
        elif re.match(r'\d{4}\.\d{2}\.\d{2}', birth_str):
            return birth_str.replace('.', '-')
        elif re.match(r'\d{4}/\d{2}/\d{2}', birth_str):
            return birth_str.replace('/', '-')
        else:
            # 숫자만 추출하여 YYYY-MM-DD 형식으로 변환
            numbers = re.findall(r'\d+', birth_str)
            if len(numbers) >= 3:
                year = numbers[0]
                month = numbers[1].zfill(2)
                day = numbers[2].zfill(2)
                return f"{year}-{month}-{day}"
    except Exception:
        pass
    
    return None

TEAM_PREFIX_TO_CODE = {
    'LG': 'LG', '두산': 'DS', 'SSG': 'SSG', '롯데': 'LT', 'KIA': 'KIA', '삼성': 'SS', '한화': 'HH', 'NC': 'NC', '키움': 'WO', 'KT': 'KT'
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
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

def build_driver() -> webdriver.Chrome:
    options = Options()
    chrome_bin = shutil.which('google-chrome') or shutil.which('google-chrome-stable') or '/usr/bin/google-chrome'
    if chrome_bin:
        options.binary_location = chrome_bin
    
    # Selenium 4.33.0 호환성을 위한 옵션들
    options.add_argument('--headless=new')
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
        # Windows 환경에서 Chrome 경로 명시적 설정
        import os
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME', '')),
        ]
        
        chrome_path = None
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_path = path
                break
        
        if chrome_path:
            options.binary_location = chrome_path
            print(f"✅ Chrome 경로 설정: {chrome_path}")
        
        # Selenium 4.x에서는 Service 객체를 사용하는 것이 권장됨
        service = Service()
        driver = webdriver.Chrome(service=service, options=options)
        print("✅ Chrome WebDriver 생성 성공")
        
    except Exception as e:
        print(f"❌ Chrome WebDriver 생성 실패: {e}")
        print("🔄 Firefox WebDriver로 대체 시도...")
        
        try:
            # Firefox로 대체
            firefox_options = webdriver.FirefoxOptions()
            firefox_options.add_argument('--headless')
            firefox_options.add_argument('--width=1920')
            firefox_options.add_argument('--height=1080')
            
            driver = webdriver.Firefox(options=firefox_options)
            print("✅ Firefox WebDriver 생성 성공")
            
        except Exception as firefox_error:
            print(f"❌ Firefox WebDriver도 실패: {firefox_error}")
            print("🚫 모든 WebDriver 생성 실패. 크롤링을 중단합니다.")
            raise Exception("WebDriver를 생성할 수 없습니다. Chrome 또는 Firefox를 설치해주세요.")
    
    try:
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined});'
        })
    except Exception:
        pass
    return driver

def parse_manager_name_from_team_info_html(html: str) -> str:
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

def parse_players_from_daum_html(html: str) -> List[dict]:
    soup = BeautifulSoup(html, 'html.parser')
    rows: List[dict] = []
    table = soup.select_one('table.tbl_teamplayer') or soup.find('table', class_='tbl_teamplayer')
    if not table:
        return rows
    for tr in table.select('tbody tr'):
        tds = tr.select('td')
        if len(tds) < 3:
            continue
        back_no = tds[0].get_text(strip=True)
        name = tds[1].get_text(strip=True)
        pos = tds[2].get_text(strip=True)
        rows.append(dict(
            p_name=name, 
            p_number=clean_numeric_value(back_no, 'int'), 
            p_position=pos, 
            p_info=''
        ))
    return rows

def parse_players_from_daum_html_by_headers(html: str) -> List[dict]:
    soup = BeautifulSoup(html, 'html.parser')
    rows: List[dict] = []
    table = (
        soup.select_one('table.tbl_teamplayer')
        or soup.find('table', class_='tbl_teamplayer')
        or soup.find('table', attrs={'summary': re.compile('선수명단')})
        or soup.find('table')
    )
    if not table:
        return rows
    headers = [th.get_text(strip=True) for th in table.select('thead th')]
    for tr in table.select('tbody tr'):
        tds = tr.select('td')
        if len(tds) < 3:
            continue
        back_no = tds[0].get_text(strip=True)
        name = tds[1].get_text(' ', strip=True)
        pos = tds[2].get_text(strip=True)
        bats = ''
        throws = ''
        if headers:
            for idx, h in enumerate(headers):
                if '투타' in h or '투·타' in h or '투타정보' in h:
                    if idx < len(tds):
                        info = tds[idx].get_text(strip=True)
                        throws = info
                    break
        rows.append(dict(
            p_name=name, 
            p_number=clean_numeric_value(back_no, 'int'), 
            p_position=pos, 
            p_info=f"{throws}{bats}"
        ))
    return rows

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
                        'p_name': name,
                        'p_number': clean_numeric_value(back_number, 'int'),
                        'p_position': position,
                        'height_cm': clean_height_cm(height),
                        'weight_kg': clean_weight_kg(weight),
                        'birth': clean_birth_date(birthdate),
                        'p_info': bats_throws,
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
        # 데이터 정제
        p_number = clean_numeric_value(player.get('p_number', ''), 'int')
        height_cm = clean_height_cm(player.get('height_cm', ''))
        # weight_kg는 이미 문자열로 처리되어 있음
        weight_kg = player.get('weight_kg', '')
        birth = clean_birth_date(player.get('birth', ''))
        
        rows.append({
            'p_name': player.get('p_name', ''),
            'p_number': p_number,
            'p_position': player.get('p_position', ''),
            'height_cm': height_cm,
            'weight_kg': weight_kg,
            'birth': birth,
            'p_info': player.get('p_info', ''),
        })
    
    return rows

def to_code_from_team_name(team_name: str) -> str:
    prefix = team_name.split()[0]
    return TEAM_PREFIX_TO_CODE.get(prefix, '')

def get_html_via_requests(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text

# def extract_stadium_from_html(html: str) -> str:
#     """HTML에서 구장 정보 추출 - 새로운 모델에서 제거됨"""
#     return ''

class Command(BaseCommand):
    help = 'KBO 팀/감독/선수 최신 데이터 수집 (Daum 사이트만 사용)'

    def add_arguments(self, parser):
        parser.add_argument('--only', type=str, help='특정 팀 코드만(e.g., LG,OB,SSG,...)')
        parser.add_argument('--sleep', type=float, default=0.5, help='요청 간 대기(초)')
        parser.add_argument('--no-browser', action='store_true', help='브라우저 없이 requests로만 수집')

    def handle(self, *args, **opts):
        only = opts.get('only')
        pause = float(opts.get('sleep') or 0.5)
        no_browser = bool(opts.get('no_browser'))

        # 데이터베이스 테이블 구조 확인 및 수정
        self.fix_database_schema()

        # 각 팀별로 독립적인 드라이버 사용
        if only:
            # 단일 팀 크롤링
            self.crawl_single_team(only, pause, no_browser)
        else:
            # 전체 팀 크롤링
            self.crawl_all_teams(pause, no_browser)

    def fix_database_schema(self):
        """데이터베이스 테이블 구조 확인 및 수정"""
        from django.db import connection
        
        try:
            with connection.cursor() as cursor:
                # weight_kg 컬럼 타입 확인
                cursor.execute("""
                    SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'kbo_player' 
                    AND COLUMN_NAME = 'weight_kg'
                """)
                
                column_info = cursor.fetchone()
                if column_info:
                    column_name, data_type, max_length = column_info
                    self.stdout.write(f"  🔍 weight_kg 컬럼 정보: {data_type}({max_length})")
                    
                    # Decimal 타입이면 VARCHAR로 변경
                    if data_type.lower() in ['decimal', 'numeric']:
                        self.stdout.write("  🔧 weight_kg 컬럼을 VARCHAR(10)으로 변경 중...")
                        cursor.execute("ALTER TABLE kbo_player MODIFY COLUMN weight_kg VARCHAR(10)")
                        self.stdout.write("  ✅ weight_kg 컬럼 타입 변경 완료")
                    else:
                        self.stdout.write("  ✅ weight_kg 컬럼이 이미 올바른 타입입니다")
                else:
                    self.stdout.write("  ⚠️ weight_kg 컬럼을 찾을 수 없습니다")
                    
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  ⚠️ 데이터베이스 스키마 수정 중 오류: {str(e)}"))
            self.stdout.write("  계속 진행합니다...")

    def crawl_single_team(self, team_code: str, pause: float, no_browser: bool):
        """단일 팀 크롤링"""
        team_data = [
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
        
        # 해당 팀 찾기
        target_team = None
        for code, name in team_data:
            if code == team_code:
                target_team = (code, name)
                break
        
        if not target_team:
            self.stdout.write(self.style.ERROR(f'팀 코드 {team_code}를 찾을 수 없습니다.'))
            return
        
        self.crawl_team(target_team[0], target_team[1], pause, no_browser)

    def crawl_all_teams(self, pause: float, no_browser: bool):
        """전체 팀 크롤링"""
        team_data = [
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

        for code, team_name in team_data:
            self.crawl_team(code, team_name, pause, no_browser)
            time.sleep(pause)

    def crawl_team(self, code: str, team_name: str, pause: float, no_browser: bool):
        """개별 팀 크롤링"""
        driver = None if no_browser else build_driver()
        
        try:
            # 기존 팀이 있는지 확인 (이름 또는 코드로)
            existing_team = None
            try:
                existing_team = Team.objects.get(team_code=code)
            except Team.DoesNotExist:
                try:
                    existing_team = Team.objects.get(team_name=team_name)
                except Team.DoesNotExist:
                    pass
            
            if existing_team:
                # 기존 팀이 있으면 코드와 이름을 모두 업데이트
                existing_team.team_code = code
                existing_team.team_name = team_name
                existing_team.save()
                team = existing_team
            else:
                # 새 팀 생성
                team = Team.objects.create(team_code=code, team_name=team_name)

            mgr_name: Optional[str] = ''
            rows: List[dict] = []
            daum_id = DAUM_TEAM_ID_MAP.get(code)
            
            if daum_id:
                daum_url = f'https://sports.daum.net/team/kbo/{daum_id}/squad'
                try:
                    if driver:
                        driver.get(daum_url)
                        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'table')))
                        rendered = driver.page_source
                        
                        # 페이지 정보 확인
                        self.stdout.write(f"  🔍 페이지 URL: {daum_url}")
                        
                        # 선수 테이블 존재 여부 확인
                        soup = BeautifulSoup(rendered, 'html.parser')
                        player_table = soup.find('table', class_='tbl_teamplayer')
                        if player_table:
                            self.stdout.write(f"  ✅ 선수 테이블 발견: tbl_teamplayer")
                        else:
                            self.stdout.write(f"  ❌ 선수 테이블(tbl_teamplayer) 발견 안됨")
                        
                        tmp_mgr = parse_manager_name_from_team_info_html(rendered)
                        if tmp_mgr:
                            mgr_name = tmp_mgr
                        # stadium 필드는 새로운 모델에서 제거됨

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
                                rows_pos = adapt_players_v2_to_rows(players_v2) or parse_players_from_daum_html_by_headers(rendered_pos)
                                if rows_pos:
                                    collected.extend(rows_pos)
                                    self.stdout.write(f"  📍 {pos_key} 포지션에서 {len(rows_pos)}명 선수 발견")
                                else:
                                    self.stdout.write(f"  ⚠️ {pos_key} 포지션에서 선수 발견 안됨")
                            except Exception as e:
                                # 탭 요소가 없거나 클릭 실패 → 다음 포지션으로 진행
                                self.stdout.write(f"  ❌ {pos_key} 포지션 토글 실패: {str(e)}")
                                continue
                        # 토글 결과가 없으면 현재 화면에서라도 파싱
                        if collected:
                            rows = collected
                            self.stdout.write(f"  ✅ 토글 방식으로 총 {len(collected)}명 선수 수집")
                        else:
                            players_v2 = parse_players_from_daum_html_v2(rendered)
                            rows = adapt_players_v2_to_rows(players_v2) or parse_players_from_daum_html_by_headers(rendered)
                            self.stdout.write(f"  🔍 현재 화면에서 {len(rows)}명 선수 파싱")
                    else:
                        daum_html = get_html_via_requests(daum_url)
                        tmp_mgr = parse_manager_name_from_team_info_html(daum_html)
                        if tmp_mgr:
                            mgr_name = tmp_mgr
                        # stadium 필드는 새로운 모델에서 제거됨
                        players_v2 = parse_players_from_daum_html_v2(daum_html)
                        rows = adapt_players_v2_to_rows(players_v2) or parse_players_from_daum_html_by_headers(daum_html)
                        self.stdout.write(f"  🌐 requests 방식으로 {len(rows)}명 선수 파싱")
                except Exception as e:
                    self.stdout.write(f"  ❌ 크롤링 오류: {str(e)}")
                    pass

            # 데이터베이스 저장 과정 상세 로깅
            self.stdout.write(f"  📊 데이터베이스 저장 시작:")
            self.stdout.write(f"    - 팀: {team.team_name} (ID: {team.team_id})")
            self.stdout.write(f"    - 감독: {mgr_name or '없음'}")
            self.stdout.write(f"    - 선수 수: {len(rows)}명")
            
            if not mgr_name or not rows:
                self.stdout.write(self.style.WARNING(f'{team.team_name} - 데이터 추출 실패 (Daum에서만 시도)'))
                return  # 데이터가 없으면 저장하지 않음

            # 감독 정보 저장
            if mgr_name:
                try:
                    manager, created = Manager.objects.update_or_create(
                        team=team, 
                        defaults={'m_name': mgr_name}
                    )
                    self.stdout.write(f"    ✅ 감독 저장: {mgr_name} ({'생성' if created else '업데이트'})")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"    ❌ 감독 저장 실패: {str(e)}"))

            # 기존 선수 데이터 삭제
            try:
                deleted_count = Player.objects.filter(team=team).count()
                Player.objects.filter(team=team).delete()
                self.stdout.write(f"    🗑️ 기존 선수 {deleted_count}명 삭제 완료")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"    ❌ 기존 선수 삭제 실패: {str(e)}"))
            
            # 데이터 최종 정제
            cleaned_rows = []
            for i, row in enumerate(rows):
                try:
                    cleaned_row = {
                        'p_name': str(row.get('p_name', '')),
                        'p_number': clean_numeric_value(row.get('p_number', ''), 'int'),
                        'p_position': str(row.get('p_position', '')),
                        'height_cm': clean_height_cm(row.get('height_cm', '')),
                        'weight_kg': clean_weight_kg(row.get('weight_kg', '')),
                        'birth': clean_birth_date(row.get('birth', '')),
                        'p_info': str(row.get('p_info', '')),
                    }
                    cleaned_rows.append(cleaned_row)
                    
                    # 첫 번째 선수 데이터 로깅
                    if i == 0:
                        self.stdout.write(f"    📝 첫 번째 선수 데이터: {cleaned_row}")
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"    ❌ 선수 {i+1}번 데이터 정제 실패: {str(e)}"))
                    continue
            
            self.stdout.write(f"    🔧 정제된 선수 데이터: {len(cleaned_rows)}명")
            
            # 선수 객체 생성 및 저장
            try:
                objs = [Player(team=team, **row) for row in cleaned_rows]
                if objs:
                    Player.objects.bulk_create(objs, batch_size=300)
                    self.stdout.write(f"    ✅ 선수 {len(objs)}명 데이터베이스 저장 완료")
                else:
                    self.stdout.write(self.style.WARNING(f"    ⚠️ 저장할 선수 데이터가 없습니다"))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"    ❌ 선수 데이터베이스 저장 실패: {str(e)}"))
                # 상세 에러 정보 출력
                import traceback
                self.stdout.write(f"    📋 에러 상세: {traceback.format_exc()}")

            # 최종 결과 로깅
            try:
                saved_players = Player.objects.filter(team=team).count()
                saved_manager = Manager.objects.filter(team=team).first()
                manager_name_to_log = saved_manager.m_name if saved_manager else '-'
                
                self.stdout.write(self.style.SUCCESS(f'{team.team_name} ✔ (감독:{manager_name_to_log}, 선수:{saved_players}명)'))
                self.stdout.write(f"    📊 최종 저장 결과: 팀 1개, 감독 1개, 선수 {saved_players}개")
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"    ❌ 최종 결과 확인 실패: {str(e)}"))
            
        finally:
            # 각 팀 크롤링 완료 후 드라이버 정리
            if driver:
                try:
                    driver.quit()
                    self.stdout.write(f"  🧹 {team_name} Chrome 드라이버 정리 완료")
                except:
                    pass