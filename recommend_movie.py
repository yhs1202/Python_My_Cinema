import requests
import random
import pandas as pd

# ======== 1. 장르 한글 ↔ ID 매핑 ========
genre_dict = {
    "28": "액션", "12": "모험", "16": "애니메이션", "35": "코미디",
    "80": "범죄", "99": "다큐멘터리", "18": "드라마", "10751": "가족",
    "27": "공포", "10749": "로맨스", "878": "SF", "53": "스릴러",
    "10752": "전쟁", "37": "서부", "14": "판타지", "36": "역사",
    "10402": "음악", "9648": "미스터리"
}

# # 한글 → ID 변환
# def get_genre_id_by_name(korean_name):
#     for id_, name in genre_dict.items():
#         if name == korean_name:
#             return id_
#     return None


def get_movies(api_key, country='ko', runtime_type=None, count=10, genre_id=None):
    """
    특정 장르의 영화 목록을 페이지 범위로 가져오는 함수
    
    :param country: ISO 639-1 국가 코드 (예: 'ko', 'en')
    :param genre_id: 장르 ID (예: '28' 액션)
    :param runtime_type: 1(60~120), 2(120~180), 3(180+)
    :param api_key: TMDb API 키
    :param genre_id: 장르 ID
    :param count: 최종 반환할 영화 수 (기본 5)
    """
    url = "https://api.themoviedb.org/3/discover/movie"
    all_movies = []

    #### Modify page range here ####
    page_range = 5
    for page_num in range(1, page_range + 1):    
        params = {
            "api_key": api_key,
            "with_original_language": country,  # 국가 코드로 필터링
            "with_genres": genre_id,
            "with_runtime.gte": 60 * runtime_type,  # minimum runtime
            "with_runtime.lte": 60 * (runtime_type + 1) if runtime_type != 3 else None,  # maximum runtime
            "language": "ko-KR",  # 한국어 데이터 요청
            "sort_by": "popularity.desc",
            "include_adult" : False,
            "page": page_num,
            "certification_country": "KR",  # 한국 등급 필터링
            "certification.lte": "15"  # 한국 19금 제외 (ALL/12/15까지만)
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"페이지 {page_num} 요청 실패: {e}")
            continue

        movies_data = response.json()
        movies = movies_data.get('results', [])

        if not movies:
            print(f"{page_num} 페이지에서 영화를 찾을 수 없습니다.")
            continue

        all_movies.extend(movies)

    # count보다 많으면 랜덤 샘플링, 아니면 그대로 반환
    # print(f"총 {len(all_movies)}개의 영화가 검색되었습니다.")
    if count and len(all_movies) > count:
        all_movies = random.sample(all_movies, count)

    return pd.DataFrame(all_movies)  # DataFrame으로 변환하여 반환


def get_data(df):
    col_list = [
    'backdrop_path',        # concatenated with 'https://image.tmdb.org/t/p/w1280'
    'genre_ids',            # list of genre IDs
    'original_language',    # e.g., 'ko' for Korean
    'overview',             # movie overview or synopsis
    'poster_path',          # concatenated with 'https://image.tmdb.org/t/p/w1280'
    'release_date',         # release date in 'YYYY-MM-DD' format
    'title',                # movie title in Korean
    'vote_average',         # average rating (0-10 scale)
    'vote_count'            # total number of votes
    ]
    df = df.drop(columns=[col for col in df.columns if col not in col_list])

    for i in range(len(df)):
        bdp_path = "https://image.tmdb.org/t/p/w1280" + df.loc[i]['backdrop_path'] if df.loc[i]['backdrop_path'] else "https://image.tmdb.org/t/p/w1280/no_image.jpg"
        # genre_names = [genre_dict.get(str(gid)) for gid in df.loc[i]['genre_ids'] if genre_dict.get(str(gid))]
        genre_names = df.loc[i]['genre_ids'] if df.loc[i]['genre_ids'] else []
        original_language = df.loc[i]['original_language'] if df.loc[i]['original_language'] else "N/A"
        overview = df.loc[i]['overview'] if df.loc[i]['overview'] else "줄거리가 없습니다."
        poster_path = "https://image.tmdb.org/t/p/w1280" + df.loc[i]['poster_path'] if df.loc[i]['poster_path'] else "https://image.tmdb.org/t/p/w1280/no_image.jpg"
        release_date = df.loc[i]['release_date'] if df.loc[i]['release_date'] else "N/A"
        title = df.loc[i]['title'] if df.loc[i]['title'] else "제목이 없습니다."
        vote_average = f"{float(df.loc[i]['vote_average']):.2f}" if df.loc[i]['vote_average'] else "N/A"
        vote_count = int(df.loc[i]['vote_count']) if df.loc[i]['vote_count'] else "N/A"

        print(f"{i+1}\n{'*'*100}")
        print(f"제목-> {title}")
        print(f"장르-> {genre_names}")
        print(f"날짜-> {release_date}")
        print(f"평점-> {vote_average}")
        print(f"투표수-> {vote_count}")
        print(f"언어-> {original_language}")
        print(f"bdp_path-> {bdp_path}")
        print(f"poster_path-> {poster_path}")
        print(f"줄거리\n {'-'*100} \n{overview}\n {'-'*100}")


    return bdp_path, genre_names, original_language, overview, poster_path, release_date, title, vote_average, vote_count

# ======== 3. 메인 실행 ========
if __name__ == "__main__":
    # Modify your TMDB API KEY here
    API_KEY = "066db65e606a576b241c3ba9050dff3f"  


    # for test
    while True:
        print(genre_dict)
        print()
        print("*"*100)
        input_lang = input("언어 입력 (ko, en 등):>> ")
        input_runtime = input("영화 길이 범위 입력 (1: 1~2h, 2: 2~3h, 3: 3h 이상):>> ")
        input_genre = input("장르 번호 입력>> ")
        recommended_movies = get_movies(API_KEY, "ko", runtime_type=1, count=10, genre_id=input_genre)
        get_data(recommended_movies)

    # genre_list = [g.strip() for g in input_genres.split(",") if g.strip()]  # ['28','35','18']
    # genre_str = ",".join(genre_list)  # "28,35,18"
    while True:
        num = input()
        df = get_movies(API_KEY, "ko", num, runtime_type=1)
        get_data(df)