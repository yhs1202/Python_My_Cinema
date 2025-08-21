# aws.py

import boto3
import requests
import hashlib

# --- 추가된 라이브러리 ---
from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
# -------------------------

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

def get_wikidata_image(wikidata_id):
    """
    Wikidata ID를 이용해 인물 이미지 URL을 가져오는 함수
    """
    if not wikidata_id:
        return None
    
    url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbgetentities",
        "ids": wikidata_id,
        "props": "claims",
        "format": "json",
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        claims = data['entities'][wikidata_id]['claims']
        if 'P18' in claims:
            image_filename = claims['P18'][0]['mainsnak']['datavalue']['value']
            image_filename = image_filename.replace(' ', '_')
            
            md5_hash = hashlib.md5(image_filename.encode('utf-8')).hexdigest()
            
            # 고화질 이미지를 위해 썸네일 크기(200px) 부분을 제거할 수 있습니다.
            return f"https://upload.wikimedia.org/wikipedia/commons/{md5_hash[0]}/{md5_hash[0:2]}/{image_filename}"
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching image from Wikidata: {e}")
        return None
    except KeyError:
        print(f"No image or claims found for Wikidata ID: {wikidata_id}")
        return None

# ----- 기존 naver_news_search 함수를 아래 nate_news_search 함수로 대체합니다 -----

def nate_news_search(query):
    """
    Selenium과 BeautifulSoup을 이용해 네이트 뉴스 검색 결과를 크롤링하는 함수
    """
    options = Options()
    options.add_argument('--headless') 
    options.add_argument('--no-sandbox')
    options.add_argument('--start-maximized')
    options.add_argument('--disable-dev-shm-usage')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    news_articles = []
    try:
        driver.get("https://news.nate.com/")
        
        # 검색창에 키워드 입력 및 검색 실행
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "input_search"))
        )
        search_box.send_keys(query)
        search_box.send_keys(Keys.ENTER)

        # 검색 결과 페이지 로딩 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "search-result"))
        )
        
        # 현재 페이지의 HTML 소스 가져오기
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # 기사 목록 선택
        articles = soup.select('ul.search-list li.items')

        if not articles:
            print(f"[{query}]에 대한 뉴스 요소를 찾을 수 없습니다.")
            return []

        # 상위 3개 기사만 가져오기
        for article in articles[:11]:
            try:
                anchor = article.select_one('a')
                if not anchor:
                    continue

                link = anchor['href']
                title = anchor.select_one('h2.tit').get_text(strip=True)
                info = anchor.select_one('span.time').get_text(strip=True) # 언론사 및 날짜 정보

                news_articles.append({
                    "title": title,
                    "url": link,
                    "source": info  # html에서 'source'로 사용되므로 'info'를 매핑
                })
            except AttributeError:
                # 구조가 다른 li가 있을 경우를 대비한 예외 처리
                print(f"정보를 가져올 수 없는 항목입니다: {article.get_text(strip=True)}")

    except Exception as e:
        print(f"네이트 뉴스 크롤링 중 오류 발생: {e}")
    finally:
        driver.quit()
        
    return news_articles

def recognize_celebrities(photo):
    client = boto3.client('rekognition')
    
    try:
        with open(photo, 'rb') as image:
            response = client.recognize_celebrities(Image={'Bytes': image.read()})
    except FileNotFoundError:
        return {"error": "파일을 찾을 수 없습니다."}

    if not response['CelebrityFaces']:
        return {"result": "감지된 유명인이 없습니다."}
    
    celebrity_list = []
    for celebrity in response['CelebrityFaces']:
        celeb_info = {
            "name": celebrity.get('Name', '알 수 없음'),
            "gender": celebrity.get('KnownGender', {}).get('Type', '알 수 없음'),
            "urls": celebrity.get('Urls', [])
        }
        
        name = celeb_info['name']
        
        wikidata_id = None
        for url in celeb_info['urls']:
            if "wikidata.org/wiki/" in url:
                wikidata_id = url.split('/')[-1]
                break
        
        if wikidata_id:
            image_url = get_wikidata_image(wikidata_id)
            celeb_info['image_url'] = image_url
        else:
            celeb_info['image_url'] = None
        
        # 정확한 검색을 위해 따옴표를 추가합니다.
        exact_query = f'"{name}"'
        
        # --- 중요: nate_news_search 함수를 호출하도록 변경 ---
        celeb_info['news'] = nate_news_search(exact_query)
        
        celebrity_list.append(celeb_info)
            
    return {"result": "success", "celebrities": celebrity_list}