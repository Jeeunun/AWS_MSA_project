from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import ElementClickInterceptedException, ElementNotInteractableException, TimeoutException
import time
from datetime import date
import pandas as pd
from dotenv import load_dotenv
import os
import pymysql

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
            INSERT INTO news (title, keyword, link)
            VALUES (%s, %s, %s)
            '''
        for row in records:
            cursor.execute(insert_sql, (row['제목'], row['키워드'], row['링크']))

        conn.commit()
        print('데이터베이스 저장완료')

    except Exception as e:
        print(e)
    finally:
        conn.close()


# 뉴스 크롤링 함수
def news_crawling(driver, url):
    # 결과 데이터 저장
    result = {'제목':[], '키워드':[], '링크':[]}

    driver.get(url) 

    while True:
        try:
            # 더보기 버튼 찾기
            more_button = driver.find_element(By.CLASS_NAME, 'link_moreview')
            
            # 버튼 누르기
            if more_button.is_displayed():
                driver.execute_script("arguments[0].click();", more_button)
                time.sleep(1.5) 

                # 스크롤 다운
                scroll_down(driver, max_scroll=10)

                # 뉴스 기사 크롤링
                news_list = driver.find_elements(By.CSS_SELECTOR, '.list_news > li')
                for news in news_list:
                    try: 
                        a_tag = news.find_element(By.TAG_NAME, 'a')
                        keyword = a_tag.get_attribute('data-tiara-tags')
                        link = a_tag.get_attribute('href')

                        title_tag = news.find_element(By.CLASS_NAME, 'tit_news')
                        title = title_tag.text

                        result['제목'].append(title)
                        result['키워드'].append(keyword)
                        result['링크'].append(link)

                    except:
                        print('연산자오류')

            else:
                break  
        except (ElementClickInterceptedException, ElementNotInteractableException, TimeoutException):
            break  
        except Exception as e:
            print("오류 발생:", e)
            break

    driver.quit()

    return result

driver = webdriver.Chrome()
news_url = f"https://sports.daum.net/baseball/news/breaking?date={''.join(str(date.today()).split('-'))}"
news_data = news_crawling(driver, news_url)

# 로컬 디렉터리 내 저장
save_data(make_dataframe(news_data), 'news')

# 데이터베이스 내 저장
save_to_db(make_dataframe(news_data))