import boto3
import requests
import hashlib

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
            
            return f"https://upload.wikimedia.org/wikipedia/commons/thumb/{md5_hash[0]}/{md5_hash[0:2]}/{image_filename}/200px-{image_filename}"
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching image from Wikidata: {e}")
        return None
    except KeyError:
        print(f"No image or claims found for Wikidata ID: {wikidata_id}")
        return None

def naver_news_search(query):
    """
    Selenium을 이용해 네이버 뉴스 검색 결과를 크롤링하는 함수
    """
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    search_url = f"https://search.naver.com/search.naver?where=news&query={query}"
    driver.get(search_url)

    news_articles = []
    try:
        wait = WebDriverWait(driver, 15)
        
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.news_wrap.api_ani_send")))

        news_elements = driver.find_elements(By.CSS_SELECTOR, "div.news_wrap.api_ani_send")
        
        if not news_elements:
            print(f"[{query}]에 대한 뉴스 요소를 찾을 수 없습니다.")
            return []

        for element in news_elements[:3]:
            # 뉴스 제목 링크를 찾는 선택자에 'a.nocr' 추가
            title_link_elements = element.find_elements(By.CSS_SELECTOR, "a.news_tit, a.nocr")
            # 언론사 정보를 찾는 선택자에 'div.info_group a.info' 추가
            source_elements = element.find_elements(By.CSS_SELECTOR, "a.info.press, div.info_group a.info")

            if title_link_elements and source_elements:
                title_link_element = title_link_elements[0]
                source_element = source_elements[0]
                
                title_spans = title_link_element.find_elements(By.CSS_SELECTOR, "span.sds-comps-text")
                if title_spans and title_spans[0].text:
                    title = title_spans[0].text
                else:
                    title = title_link_element.text

                url = title_link_element.get_attribute("href")
                source = source_element.text
                
                news_articles.append({
                    "title": title,
                    "url": url,
                    "source": source
                })
            else:
                print(f"뉴스 기사 상세 정보를 찾을 수 없습니다: {element.text}")
                
    except Exception as e:
        print(f"네이버 뉴스 크롤링 중 오류 발생: {e}")
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
        celeb_info['news'] = naver_news_search(exact_query)
        
        celebrity_list.append(celeb_info)
        
    return {"result": "success", "celebrities": celebrity_list}