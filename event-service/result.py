# 패키지 설치
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

# 데이터 저장 함수
def save_data(data, name):
    df = make_dataframe(data)
    save_path = f'./data/{name}.csv'
    df.to_csv(save_path, index=False, encoding='utf-8')


# 데이터베이스 연결, 저장 함수
def save_to_db(data):
    load_dotenv()
    records = data.to_dict(orient='records')

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
        insert_sql = '''
            INSERT INTO result (team1, team1_score, team2, team2_score, time, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            '''
        for row in records:
            cursor.execute(insert_sql, (row['team1'], int(row['team1_score']) if row['team1_score'] else None, row['team2'], int(row['team2_score']) if row['team2_score'] else None, (row['time']), row['status']))

        conn.commit()
        print('데이터베이스 저장완료')

    except Exception as e:
        print(e)
    finally:
        conn.close()


# 경기 일정 및 결과 크롤링
def result_crawling(driver, url):
    # 결과값 저장
    result_data = {'team1':[], 'team1_score':[], 'team2':[], 'team2_score':[], 'time':[], 'status':[]}

    driver.get(url)
    wait = WebDriverWait(driver, 10)

    # 날짜 선택
    data_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.btn_date.btn_prev')))
    for _ in range(2): # 2번클릭 (종료된 경기 선택위함) -> 수정하려면 1번 클릭하면 된다.
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


driver = webdriver.Chrome()
sports_url = "https://sports.daum.net/"
result = result_crawling(driver, sports_url)


# 로컬 디렉터리 내 저장
save_data(result, '경기결과')

# 데이터베이스 내 저장
save_to_db(make_dataframe(result))