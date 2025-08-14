import requests
import random

# ======== 1. 장르 한글 ↔ ID 매핑 ========
genre_dict = {
    "28": "액션",
    "12": "모험",
    "16": "애니메이션",
    "35": "코미디",
    "80": "범죄",
    "99": "다큐멘터리",
    "18": "드라마",
    "10751": "가족",
    "14": "판타지",
    "27": "공포",
    "10749": "로맨스",
    "878": "SF",
    "53": "스릴러"
}

# 한글 → ID 변환
def get_genre_id_by_name(korean_name):
    for id_, name in genre_dict.items():
        if name == korean_name:
            return id_
    return None

# ID → 한글 변환
def get_genre_name_by_id(genre_id):
    return genre_dict.get(str(genre_id), "알 수 없는 장르")

# ======== 2. TMDB API로 장르별 영화 검색 ========
def get_movies_by_genre(genre_id, api_key, count=5):
    url = "https://api.themoviedb.org/3/discover/movie"
    params = {
        "api_key": api_key,
        "with_genres": genre_id,
        "language": "ko-KR",            # 한국어 데이터 요청
        "sort_by": "popularity.desc",
        "page": 1
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        print("API 요청 실패:", response.status_code)
        return []

    movies = response.json().get('results', [])
    if not movies:
        print("해당 장르의 영화를 찾을 수 없습니다.")
        return []

    return random.sample(movies, min(count, len(movies)))

# ======== 3. 메인 실행 ========
if __name__ == "__main__":
    API_KEY = "1a73c72e2b71b20c1d52a62b77399d65"  # ← 여기 본인 TMDB API 키 입력
