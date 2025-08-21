# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

def get_film_festivals_with_selenium():
    all_festivals = []
    
    # 웹 드라이버 설정 (ChromeDriver를 자동으로 설치하고 관리)
    try:
        # 0821 modified / Compatible with Chrome in CLI mode
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--remote-debugging-port=0")
        options.add_argument("--user-data-dir=/tmp/selenium_profile")
        options.add_argument("--window-size=1200,800")
        driver = webdriver.Chrome(options=options)
        
    except Exception as e:
        print(f"웹 드라이버 설정 중 오류 발생: {e}")
        return []

    url = "https://www.kobis.or.kr/kobis/business/mast/fest/searchUserFestInfoList.do"
    driver.maximize_window()  # modified in 0821_11xx
    driver.get(url)
    
    # 크롤링할 최대 페이지 수 (예: 10페이지)
    max_pages = 2 
    
    for page_num in range(1, max_pages + 1):
        try:
            print(f"크롤링 중... 페이지: {page_num}")
            
            # 현재 페이지의 HTML 소스를 가져옵니다.
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            table_rows = soup.select('table.tbl_comm > tbody > tr')
            
            if not table_rows:
                print("더 이상 데이터가 없습니다. 크롤링을 종료합니다.")
                break
            
            for row in table_rows:
                cols = row.find_all('td')
                if len(cols) >= 9:
                    website_link_tag = cols[7].find('a')
                    website = website_link_tag['href'] if website_link_tag else None
                    
                    festival_info = {
                        'title': cols[0].get_text(strip=True),
                        'location': cols[3].get_text(strip=True),
                        'period': cols[4].get_text(strip=True),
                        'website': website,
                    }
                    all_festivals.append(festival_info)
            
            # 다음 페이지 버튼 클릭 (페이지네이션)
            # 페이지 번호가 담긴 a 태그를 찾아서 클릭합니다.
            if page_num < max_pages:
                next_page_link = driver.find_element(By.LINK_TEXT, str(page_num + 1))
                next_page_link.click()
                time.sleep(2) # 페이지 로딩을 기다립니다.

        except Exception as e:
            print(f"페이지 {page_num} 크롤링 중 오류 발생: {e}")
            break

    driver.quit() # 작업이 끝나면 브라우저를 닫습니다.
    return all_festivals

# 함수 테스트
if __name__ == '__main__':
    festival_list = get_film_festivals_with_selenium()
    if festival_list:
        print(f"총 {len(festival_list)}개의 영화제 정보를 성공적으로 가져왔습니다.")
    else:
        print("영화제 데이터를 찾을 수 없습니다.")