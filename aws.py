import boto3

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
        celebrity_info = {
            "name": celebrity.get('Name', '알 수 없음'),
            "gender": celebrity.get('KnownGender', {}).get('Type', '알 수 없음'),
            "urls": celebrity.get('Urls', [])
        }
        celebrity_list.append(celebrity_info)
        
    return {"result": "success", "celebrities": celebrity_list}