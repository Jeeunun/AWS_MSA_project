# 패키지 설치
from django.core.management.base import BaseCommand
import os
import json
import re
import pandas as pd
import time
import warnings
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
warnings.filterwarnings("ignore")
import pymysql
from dotenv import load_dotenv
from event.models import TotalRank, AttackRank, DefendRank
from django.db import connection

class Command(BaseCommand):
    help = '구단 순위 크롤링하여 이벤트 DB에 저장'

    def handle(self, *args, **options):
        driver = webdriver.Chrome()
        url = "https://sports.daum.net/record/KBO"
        total, attack, defend = self.rank_crawling(driver, url)

        # 기존 데이터 삭제 및 id 값 초기화(mariadb 사용시 truncate 가능)
        with connection.cursor() as cursor:
            cursor.execute('TRUNCATE TABLE event_totalrank')
            cursor.execute('TRUNCATE TABLE event_defendrank')
            cursor.execute('TRUNCATE TABLE event_attackrank')

        # 전체순위
        for row in total:
            TotalRank.objects.create(**row)

        # attack
        for row in attack:
            AttackRank.objects.create(**row)

        # defend
        for row in defend:
            DefendRank.objects.create(**row)

        self.stdout.write(self.style.SUCCESS('구단 순위 크롤링 및 저장 완료'))
        
    # 스크롤 다운 함수
    def scroll_down(self, driver, max_scroll=10):
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(max_scroll):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height


    # 순위 크롤링 함수
    def rank_crawling(self, driver, url):
        # 데이터 저장 딕셔너리
        total = {'순위': [], '팀': [], '경기': [], '승': [], '무': [], '패':[],
                '승률': [], '게임차': [], '연속': []}

        attack = {'순위': [], '팀': [], '타수': [], '안타': [], '2타': [], '3타': [], '홈런': [],
                '타점': [], '득점': [], '도루': [], '사사구': [], '삼진': [], '병살': [],
                '타율': [], '출루율': [], '장타율': [], 'OPS': []}

        defend = {'순위': [], '팀': [], '이닝': [], '피안타': [], '피홈런': [], '실점': [],
                '자책': [], '사사구': [], '탈삼진': [], '평균자책': [], '실책': [],
                'WHIP': [], 'QS': [], '홀드': [], '세이브': []}


        driver.get(url)
        time.sleep(3)


        boxes = driver.find_elements(By.CLASS_NAME, 'tbl_record')
        texts = [b.text for b in boxes]


        # total
        lines = texts[0].split('\n')
        i = 0
        while i < len(lines):
            if lines[i].strip().isdigit():
                순위 = lines[i].strip()
                팀 = lines[i + 1].strip()
                기록 = lines[i + 2].strip().split()

                total['순위'].append(순위)
                total['팀'].append(팀)
                total['경기'].append(기록[0])
                total['승'].append(기록[1])
                total['무'].append(기록[2])
                total['패'].append(기록[3])
                total['승률'].append(기록[4])
                total['게임차'].append(기록[5])
                total['연속'].append(기록[6])
                i += 3
            else:
                i += 1

        # attack
        lines = texts[1].split('\n')
        i = 0
        while i < len(lines):
            if lines[i].strip().isdigit():
                순위 = lines[i].strip()
                팀 = lines[i + 1].strip()
                기록 = lines[i + 2].strip().split()

                attack['순위'].append(순위)
                attack['팀'].append(팀)
                attack['타수'].append(기록[0])
                attack['안타'].append(기록[1])
                attack['2타'].append(기록[2])
                attack['3타'].append(기록[3])
                attack['홈런'].append(기록[4])
                attack['타점'].append(기록[5])
                attack['득점'].append(기록[6])
                attack['도루'].append(기록[7])
                attack['사사구'].append(기록[8])
                attack['삼진'].append(기록[9])
                attack['병살'].append(기록[10])
                attack['타율'].append(기록[11])
                attack['출루율'].append(기록[12])
                attack['장타율'].append(기록[13])
                attack['OPS'].append(기록[14])
                i += 3
            else:
                i += 1

        self.scroll_down(driver, max_scroll=10)

        # defend
        lines = texts[2].split('\n')
        i = 0
        while i < len(lines):
            if lines[i].strip().isdigit():
                순위 = lines[i].strip()
                팀 = lines[i + 1].strip()
                기록 = lines[i + 2].strip().split()

                defend['순위'].append(순위)
                defend['팀'].append(팀)

                if '/' in 기록[1]:  
                    이닝 = 기록[0] + ' ' + 기록[1]
                    offset = 0
                else: 
                    이닝 = 기록[0]
                    offset = -1  

                defend['이닝'].append(이닝)
                try:
                    defend['피안타'].append(기록[2 + offset])
                    defend['피홈런'].append(기록[3 + offset])
                    defend['실점'].append(기록[4 + offset])
                    defend['자책'].append(기록[5 + offset])
                    defend['사사구'].append(기록[6 + offset])
                    defend['탈삼진'].append(기록[7 + offset])
                    defend['평균자책'].append(기록[8 + offset])
                    defend['실책'].append(기록[9 + offset])
                    defend['WHIP'].append(기록[10 + offset])
                    defend['QS'].append(기록[11 + offset])
                    defend['홀드'].append(기록[12 + offset])
                    defend['세이브'].append(기록[13 + offset])
                except IndexError:
                    print(f"IndexError 팀: {팀}, 기록: {기록}")
                i += 3
            else:
                i += 1

        # 열기반 → 행기반 변환
        total_list = [
            {
                'rank': int(total['순위'][i]),
                'team': total['팀'][i],
                'games': int(total['경기'][i]),
                'wins': int(total['승'][i]),
                'lose': int(total['패'][i]),
                'rate': float(total['승률'][i]),
                'gb': float(total['게임차'][i]) if total['게임차'][i] != '-' else 0.0,
                'streak': total['연속'][i],
            }
            for i in range(len(total['순위']))
        ]

        attack_list = [
            {
                'rank': int(attack['순위'][i]),
                'team': attack['팀'][i],
                'at_bats': int(attack['타수'][i]),
                'hits': int(attack['안타'][i]),
                'doubles': int(attack['2타'][i]),
                'triples': int(attack['3타'][i]),
                'home_runs': int(attack['홈런'][i]),
                'rbi': int(attack['타점'][i]),
                'runs_scored': int(attack['득점'][i]),
                'stolen_bases': int(attack['도루'][i]),
                'walks_hit_by_pitch': int(attack['사사구'][i]),
                'strikeouts': int(attack['삼진'][i]),
                'double_plays': int(attack['병살'][i]),
                'batting_avg': float(attack['타율'][i]),
                'obp': float(attack['출루율'][i]),
                'slg': float(attack['장타율'][i]),
                'ops': float(attack['OPS'][i]),
            }
            for i in range(len(attack['순위']))
        ]

        defend_list = [
            {
                'rank': int(defend['순위'][i]),
                'team': defend['팀'][i],
                'innings': defend['이닝'][i],
                'hits_allowed': int(defend['피안타'][i]),
                'home_runs_allowed': int(defend['피홈런'][i]),
                'runs_allowed': int(defend['실점'][i]),
                'earned_runs': int(defend['자책'][i]),
                'walks_hit_by_pitch': int(defend['사사구'][i]),
                'strikeouts': int(defend['탈삼진'][i]),
                'errors': int(defend['실책'][i]),
                'whip': float(defend['WHIP'][i]),
                'qs': float(defend['QS'][i]),
                'saves': int(defend['세이브'][i]),
            }
            for i in range(len(defend['순위']))
        ]

        return total_list, attack_list, defend_list 

