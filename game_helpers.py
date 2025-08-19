import os
import requests
import random
from dotenv import load_dotenv
from flask import jsonify

# .env 파일에서 환경 변수(API 키)를 로드합니다.
load_dotenv()

def get_popular_movies():
    """TMDB API를 사용해 인기 영화 목록 9개를 안전하게 가져오는 함수"""
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        print("오류: TMDB_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
        return None

    random_page = random.randint(1, 10)
    url = (f"https://api.themoviedb.org/3/discover/movie?"
           f"api_key={api_key}"
           f"&language=ko-KR"
           f"&sort_by=popularity.desc"
           f"&page={random_page}"
           f"&with_watch_monetization_types=flatrate")

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()['results']
        
        movies = []
        for movie in data:
            if movie.get('poster_path') and movie.get('release_date'):
                movies.append({
                    'id': movie['id'],
                    'title': movie['title'],
                    'poster_path': movie['poster_path'],
                    'release_date': movie['release_date']
                })
            if len(movies) == 9:
                break
        
        return movies if len(movies) == 9 else None

    except requests.exceptions.RequestException as e:
        print(f"API 요청 중 오류가 발생했습니다: {e}")
        return None

def process_game_movies():
    """
    게임용 영화 목록을 가져와서 API 응답 형식(JSON)으로 만드는 함수
    """
    # 1. 영화 데이터 가져오기
    movies = get_popular_movies()

    # 2. 성공/실패에 따라 다른 JSON 응답 생성
    if movies:
        # 성공 시
        return jsonify({
            "result": "success",
            "movies": movies
        })
    else:
        # 실패 시
        return jsonify({
            "result": "error",
            "message": "Failed to load movies"
        }), 500 # HTTP 상태 코드 500 (Internal Server Error)