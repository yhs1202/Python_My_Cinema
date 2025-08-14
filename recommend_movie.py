import requests
import random

# ======== 1. 장르 한글 ↔ ID 매핑 ========
genre_dict = {
    "28": "액션", "12": "모험", "16": "애니메이션", "35": "코미디",
    "80": "범죄", "99": "다큐멘터리", "18": "드라마", "10751": "가족",
    "14": "판타지", "27": "공포", "10749": "로맨스", "878": "SF",
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
        "language": "ko-KR",  # 한국어 데이터 요청
        "sort_by": "popularity.desc",
        "page": 1
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # 200 OK 상태 코드가 아닐 경우 예외 발생
    except requests.exceptions.RequestException as e:
        print(f"API 요청 실패: {e}")
        return []

    movies_data = response.json()
    movies = movies_data.get('results', [])
    
    if not movies:
        print("해당 장르의 영화를 찾을 수 없습니다.")
        return []

    # movies 리스트의 영화 수가 count보다 적을 경우, 가능한 만큼만 샘플링
    return random.sample(movies, min(count, len(movies)))

# ======== 3. 메인 실행 ========
if __name__ == "__main__":
    # ▼▼▼▼▼ 본인의 TMDB API 키로 교체해주세요 ▼▼▼▼▼
    API_KEY = "1a73c72e2b71b20c1d52a62b77399d65"  
    # ▲▲▲▲▲ 본인의 TMDB API 키로 교체해주세요 ▲▲▲▲▲

    # 사용자로부터 장르 입력받기
    print("다음 장르 중 하나를 선택하세요:")
    print(', '.join(genre_dict.values()))
    input_genre = input("장르를 입력하세요: ")

    # 입력된 장르 이름으로 장르 ID 찾기
    genre_id = get_genre_id_by_name(input_genre)

    if genre_id:
        print(f"\n'{input_genre}' 장르의 인기 영화 5편을 추천합니다.\n")
        recommended_movies = get_movies_by_genre(genre_id, API_KEY)
        
        if recommended_movies:
            for i, movie in enumerate(recommended_movies, 1):
                rating = movie.get('vote_average', '정보 없음')
                print(f"{i}. {movie.get('title', '제목 없음')}")
                print(f"   - 평점: {rating} /10")
                print(f"   - 줄거리: {movie.get('overview', '정보 없음')}\n")
    else:
        print("유효하지 않은 장르입니다. 다시 시도해주세요.")

