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

# 스크롤 다운 함수
def scroll_down(driver, max_scroll=10):
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(max_scroll):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

# 데이터프레임 변환 함수
def make_dataframe(data):
    df = pd.DataFrame(data)
    return df

# 데이터 로컬 디렉터리 내 저장 함수
def save_data(data, name):
    save_path = f'./data/{name}.csv'
    data.to_csv(save_path, index=False, encoding='utf-8')


# 데이터베이스 연결, 저장 함수
def save_to_db(total, attack, defend):
    load_dotenv()
    total_records = total.to_dict(orient='records')
    attack_records = attack.to_dict(orient='records')
    defend_records = defend.to_dict(orient='records')

    # DB연결
    conn = pymysql.connect(
        host = os.getenv('HOST'),
        user = os.getenv('USER_NAME'),
        password=os.getenv('PASSWORD'),
        db=os.getenv('DB_NAME'),
        port=int(os.getenv('PORT')),
        charset='utf8mb4'
    )

    try: 
        cursor = conn.cursor()
        total_insert_sql = '''
            INSERT INTO total_rank (rank, team, games, win, lose, rate, gb, streak)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            '''
        for row in total_records:
            cursor.execute(total_insert_sql, ( row['순위'], row['팀'], row['경기'], row['승'], row['패'], row['승률'], row['게임차'], row['연속']))


        attack_insert_sql = '''
            INSERT INTO attack_rank (rank, team, at_bats, hits, doubles, triples, home_runs, rbi, runs_scored, stolen_bases, walks_hit_by_pitch, strikeout, double_plays, batting_avg, obp, slg, ops)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            '''
        for row in attack_records:
            cursor.execute(attack_insert_sql, (
                row['순위'], row['팀'], row['타수'], row['안타'], row['2타'], row['3타'], row['홈런'],
                row['타점'], row['득점'], row['도루'], row['사사구'], row['삼진'], row['병살'],
                row['타율'], row['출루율'], row['장타율'], row['OPS']
            ))
        
        defend_insert_sql = '''
            INSERT INTO defend_rank (rank, team, innings, hits_allowed, home_runs_allowed, runs_allowed, earned_runs, walks_hit_by_pitch, strikeouts, era, errors, whip, qs, holds, saves)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            '''
        for row in defend_records:
            cursor.execute(defend_insert_sql, (
                row['순위'], row['팀'], row['이닝'], row['피안타'], row['피홈런'], row['실점'],
                row['자책'], row['사사구'], row['탈삼진'], row['평균자책'], row['실책'],
                row['WHIP'], row['QS'], row['홀드'], row['세이브']
            ))


        conn.commit()
        print('데이터베이스 저장완료')

    except Exception as e:
        print(e)
    finally:
        conn.close()


# 순위 크롤링 함수
def rank_crawling(driver, url):
    # 데이터 저장 딕셔너리
    종합순위 = {'순위': [], '팀': [], '경기': [], '승': [], '무': [], '패':[],
            '승률': [], '게임차': [], '연속': []}

    공격순위 = {'순위': [], '팀': [], '타수': [], '안타': [], '2타': [], '3타': [], '홈런': [],
            '타점': [], '득점': [], '도루': [], '사사구': [], '삼진': [], '병살': [],
            '타율': [], '출루율': [], '장타율': [], 'OPS': []}

    수비순위 = {'순위': [], '팀': [], '이닝': [], '피안타': [], '피홈런': [], '실점': [],
            '자책': [], '사사구': [], '탈삼진': [], '평균자책': [], '실책': [],
            'WHIP': [], 'QS': [], '홀드': [], '세이브': []}


    driver.get(url)
    time.sleep(3)


    boxes = driver.find_elements(By.CLASS_NAME, 'tbl_record')
    texts = [b.text for b in boxes]


    # 종합순위
    lines = texts[0].split('\n')
    i = 0
    while i < len(lines):
        if lines[i].strip().isdigit():
            순위 = lines[i].strip()
            팀 = lines[i + 1].strip()
            기록 = lines[i + 2].strip().split()

            종합순위['순위'].append(순위)
            종합순위['팀'].append(팀)
            종합순위['경기'].append(기록[0])
            종합순위['승'].append(기록[1])
            종합순위['무'].append(기록[2])
            종합순위['패'].append(기록[3])
            종합순위['승률'].append(기록[4])
            종합순위['게임차'].append(기록[5])
            종합순위['연속'].append(기록[6])
            i += 3
        else:
            i += 1

    # 공격순위
    lines = texts[1].split('\n')
    i = 0
    while i < len(lines):
        if lines[i].strip().isdigit():
            순위 = lines[i].strip()
            팀 = lines[i + 1].strip()
            기록 = lines[i + 2].strip().split()

            공격순위['순위'].append(순위)
            공격순위['팀'].append(팀)
            공격순위['타수'].append(기록[0])
            공격순위['안타'].append(기록[1])
            공격순위['2타'].append(기록[2])
            공격순위['3타'].append(기록[3])
            공격순위['홈런'].append(기록[4])
            공격순위['타점'].append(기록[5])
            공격순위['득점'].append(기록[6])
            공격순위['도루'].append(기록[7])
            공격순위['사사구'].append(기록[8])
            공격순위['삼진'].append(기록[9])
            공격순위['병살'].append(기록[10])
            공격순위['타율'].append(기록[11])
            공격순위['출루율'].append(기록[12])
            공격순위['장타율'].append(기록[13])
            공격순위['OPS'].append(기록[14])
            i += 3
        else:
            i += 1

    scroll_down(driver, max_scroll=10)

    # 수비순위
    lines = texts[2].split('\n')
    i = 0
    while i < len(lines):
        if lines[i].strip().isdigit():
            순위 = lines[i].strip()
            팀 = lines[i + 1].strip()
            기록 = lines[i + 2].strip().split()

            수비순위['순위'].append(순위)
            수비순위['팀'].append(팀)

            if '/' in 기록[1]:  
                이닝 = 기록[0] + ' ' + 기록[1]
                offset = 0
            else: 
                이닝 = 기록[0]
                offset = -1  

            수비순위['이닝'].append(이닝)
            try:
                수비순위['피안타'].append(기록[2 + offset])
                수비순위['피홈런'].append(기록[3 + offset])
                수비순위['실점'].append(기록[4 + offset])
                수비순위['자책'].append(기록[5 + offset])
                수비순위['사사구'].append(기록[6 + offset])
                수비순위['탈삼진'].append(기록[7 + offset])
                수비순위['평균자책'].append(기록[8 + offset])
                수비순위['실책'].append(기록[9 + offset])
                수비순위['WHIP'].append(기록[10 + offset])
                수비순위['QS'].append(기록[11 + offset])
                수비순위['홀드'].append(기록[12 + offset])
                수비순위['세이브'].append(기록[13 + offset])
            except IndexError:
                print(f"IndexError 팀: {팀}, 기록: {기록}")
            i += 3
        else:
            i += 1

    total = make_dataframe(종합순위)
    attack = make_dataframe(공격순위)
    defend = make_dataframe(수비순위)

    return total, attack, defend



driver = webdriver.Chrome()
rank_url = "https://sports.daum.net/record/KBO"
total, attack, defend = rank_crawling(driver, rank_url)

# 로컬 디렉터리 내 저장
save_data(total, '종합순위')
save_data(attack, '공격순위')
save_data(defend, '수비순위')

# 데이터베이스 내 저장
save_to_db(total, attack, defend)