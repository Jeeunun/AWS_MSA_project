# 패키지 설치
from django.core.management.base import BaseCommand
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
import os
from django.db import connection
from event.models import Result

class Command(BaseCommand):
    help = '경기결과 크롤링하여 이벤트 DB에 저장'

    def handle(self, *args, **options):
        driver = webdriver.Chrome()
        url = "https://sports.daum.net/"
        result = self.result_crawling(driver, url)

        # 기존 데이터 삭제 및 id 값 초기화(mariadb 사용시 truncate 가능)
        with connection.cursor() as cursor:
            cursor.execute('TRUNCATE TABLE event_result')
            
        for team1, team1_score, team2, team2_score, time, status, win in zip(result['team1'], result['team1_score'], result['team2'], result['team2_score'], result['time'], result['status'],result['win']):
            Result.objects.get_or_create(team1=team1, team1_score=team1_score, team2=team2, team2_score=team2_score, time=time, status=status, win=win)

        self.stdout.write(self.style.SUCCESS('경기결과 크롤링 및 저장 완료'))

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


    # 경기 일정 및 결과 크롤링
    def result_crawling(self, driver, url):
        # 결과값 저장
        result_data = {'team1':[], 'team1_score':[], 'team2':[], 'team2_score':[], 'time':[], 'status':[], 'win':[]}

        driver.get(url)
        wait = WebDriverWait(driver, 10)

        # 날짜 선택
        data_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.btn_date.btn_prev')))
        for _ in range(1): # 1번클릭 (종료된 경기 선택위함) 
            if data_button.is_displayed():
                driver.execute_script("arguments[0].click()", data_button)

        # 리그 선택 버튼 클릭
        league_button = wait.until(EC.element_to_be_clickable((By.ID, 'selectLeagueText')))
        driver.execute_script("arguments[0].click();", league_button)

        # KBO 클릭
        kbo_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'li[data-league="KBO"] a')))
        driver.execute_script("arguments[0].click();", kbo_button)
        time.sleep(2)

        # box.text 크롤링
        while True:
            try:
                box = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'bundle_sched')))
                lines = box.text.strip().split('\n')

                # 6줄씩 묶기
                chunks = [lines[i:i+6] for i in range(0, len(lines), 7)]

                for chunk in chunks:
                    print(chunk)
                    result_data['status'].append(chunk[0])
                    if ':' in chunk[1]:
                        result_data['time'].append(chunk[1])
                        result_data['team1_score'].append(None)
                        result_data['team1'].append(chunk[3])
                        result_data['team2_score'].append(None)
                        result_data['team2'].append(chunk[4])
                    else:
                        result_data['time'].append(None)
                        result_data['team1_score'].append(chunk[2])
                        result_data['team1'].append(chunk[3])
                        result_data['team2_score'].append(chunk[4])
                        result_data['team2'].append(chunk[5])

                        # 점수 문자열을 int형으로 변환
                        try:
                            team1_score = int(chunk[2])
                            team2_score = int(chunk[4])

                            if team1_score > team2_score:
                                result_data['win'].append(chunk[3])
                            elif team1_score < team2_score:
                                result_data['win'].append(chunk[5])
                            else:
                                result_data['win'].append('무승부')
                        except ValueError:
                            result_data['win'].append(None)


            except Exception as e:
                print("box 크롤링 실패:", e)
                break

            # 다음 버튼 클릭
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, 'button.btn_page.btn_next')
                # 다음 버튼이 보일 때만 클릭
                if next_button.is_displayed():
                    driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(2)
                else:
                    break
            except Exception as e:
                print("다음 버튼 클릭 실패:", e)
                break

        driver.quit()

        return result_data