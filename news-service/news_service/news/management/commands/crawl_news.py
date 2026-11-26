from django.core.management.base import BaseCommand
from django.db import connection
from news.models import News
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import ElementClickInterceptedException, ElementNotInteractableException, TimeoutException
from datetime import date
import time

from news.models import News  # models.py에서 News 테이블 불러오기

class Command(BaseCommand):
    help = "크롤링하여 뉴스 DB에 저장"

    def handle(self, *args, **kwargs):
        driver = webdriver.Chrome()
        url = f"https://sports.daum.net/baseball/news/breaking?date={''.join(str(date.today()).split('-'))}"
        result = self.news_crawling(driver, url)
        
        # 기존 데이터 삭제 및 id값 초기화 (mariadb사용시)
        with connection.cursor() as cursor:
            cursor.execute('TRUNCATE TABLE news_news;')

        for title, keyword, link in zip(result['제목'], result['키워드'], result['링크']):
            News.objects.get_or_create(title=title, keyword=keyword, link=link)

        self.stdout.write(self.style.SUCCESS('뉴스 크롤링 및 저장 완료'))

    def scroll_down(self, driver, max_scroll=10):
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(max_scroll):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def news_crawling(self, driver, url):
        result = {'제목':[], '키워드':[], '링크':[]}
        driver.get(url)

        while True:
            try:
                more_button = driver.find_element(By.CLASS_NAME, 'link_moreview')

                if more_button.is_displayed():
                    driver.execute_script("arguments[0].click();", more_button)
                    time.sleep(1.5)
                    self.scroll_down(driver, max_scroll=10)

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
                            print('파싱 오류')
                else:
                    break
            except (ElementClickInterceptedException, ElementNotInteractableException, TimeoutException):
                break
            except Exception as e:
                print("오류 발생:", e)
                break

        driver.quit()
        return result
