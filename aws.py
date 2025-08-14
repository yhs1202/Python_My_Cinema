import boto3
import requests

def get_wikidata_image(wikidata_id):
    """
    Wikidata ID를 이용해 인물 이미지 URL을 가져오는 함수
    """
    if not wikidata_id:
        return None
    
    # Wikidata API 엔드포인트
    url = "https://www.wikidata.org/w/api.php"
    
    # API 요청 파라미터
    params = {
        "action": "wbgetentities",
        "ids": wikidata_id,
        "props": "claims",
        "format": "json",
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        # P18 (image) 속성에서 이미지 파일 이름을 추출
        claims = data['entities'][wikidata_id]['claims']
        if 'P18' in claims:
            # 첫 번째 이미지 파일 이름 가져오기
            image_filename = claims['P18'][0]['mainsnak']['datavalue']['value']
            
            # 파일 이름을 이용해 Commons Media 이미지 URL 생성
            # 이미지 파일 이름은 공백을 _로 바꿔줘야 합니다.
            image_filename = image_filename.replace(' ', '_')
            
            # Commons Media 이미지 URL
            # md5 해시를 이용한 이미지 경로 생성
            import hashlib
            md5_hash = hashlib.md5(image_filename.encode('utf-8')).hexdigest()
            
            return f"https://upload.wikimedia.org/wikipedia/commons/thumb/{md5_hash[0]}/{md5_hash[0:2]}/{image_filename}/200px-{image_filename}"
            
    except Exception as e:
        print(f"Error fetching image from Wikidata: {e}")
        return None

def recognize_celebrities(photo):
    client = boto3.client('rekognition')
    
    try:
        with open(photo, 'rb') as image:
            response = client.recognize_celebrities(Image={'Bytes': image.read()})
    except FileNotFoundError:
        return {"error": "파일을 찾을 수 없습니다."}

    # 유명인이 감지되지 않았을 때
    if not response['CelebrityFaces']:
        return {"result": "감지된 유명인이 없습니다."}
    
    # 감지된 유명인 정보 리스트
    celebrity_list = []
    for celebrity in response['CelebrityFaces']:
        celeb_info = {
            "name": celebrity.get('Name', '알 수 없음'),
            "gender": celebrity.get('KnownGender', {}).get('Type', '알 수 없음'),
            "urls": celebrity.get('Urls', [])
        }
        # Wikidata URL에서 ID를 추출하여 이미지 검색
        wikidata_id = None
        for url in celeb_info['urls']:
            if "wikidata.org/wiki/" in url:
                wikidata_id = url.split('/')[-1]
                break
        
        # Wikidata API를 호출해 이미지 URL 가져오기
        if wikidata_id:
            image_url = get_wikidata_image(wikidata_id)
            celeb_info['image_url'] = image_url
        else:
            celeb_info['image_url'] = None
        
        celebrity_list.append(celeb_info)
        
    return {"result": "success", "celebrities": celebrity_list}