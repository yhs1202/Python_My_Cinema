import requests
import pandas as pd
from flask import render_template, request


# ======== 1. 장르 한글 ↔ ID 매핑 ========
genre_dict = {
    "28": "액션", "12": "모험", "16": "애니메이션", "35": "코미디",
    "80": "범죄", "99": "다큐멘터리", "18": "드라마", "10751": "가족",
    "27": "공포", "10749": "로맨스", "878": "SF", "53": "스릴러",
    "10752": "전쟁", "37": "서부", "14": "판타지", "36": "역사",
    "10402": "음악", "9648": "미스터리"
}

# Modify your TMDB API KEY here
################################################
TMDB_API_KEY = "066db65e606a576b241c3ba9050dff3f"  
################################################

def get_movies(api_key, genre_id=None, runtime_type=None, rating=None, country='ko') -> pd.DataFrame:
    """
    특정 장르의 영화 목록을 페이지 범위로 가져오는 함수
    
    :param country: ISO 639-1 국가 코드 (예: 'ko', 'en', 'ja')
    :param genre_id: 장르 ID (예: '28' 액션)
    :param runtime_type: 1(60~120), 2(120~180), 3(180+)
    :param api_key: TMDb API 키
    :param genre_id: 장르 ID
    :param count: 최종 반환할 영화 수
    """
    url = "https://api.themoviedb.org/3/discover/movie"
    all_movies = []

    #### Modify page range here ####
    page_range = 5

    # multiple countries processing
    countries = country.split(",") if country else ['ko']
    for country in countries:
        for page_num in range(1, page_range + 1):    
            params = {
                "api_key": api_key,
                "with_genres": genre_id,
                "with_runtime.gte": 60 * runtime_type,  # minimum runtime
                "with_runtime.lte": 60 * (runtime_type + 1) if runtime_type != 3 else None,  # maximum runtime
                "vote_average.gte": rating,  # 최소 평점 5점 이상
                "with_original_language": country,  # 국가 코드로 필터링
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
                break

            all_movies.extend(movies)

    # # count보다 많으면 랜덤 샘플링, 아니면 그대로 반환
    # # print(f"총 {len(all_movies)}개의 영화가 검색되었습니다.")
    # if count and len(all_movies) > count:
    #     all_movies = random.sample(all_movies, count)

    return pd.DataFrame(all_movies)  # DataFrame으로 변환하여 반환


def get_data(df: pd.DataFrame)-> list:
    col_list = [
    'backdrop_path',        # concatenated with 'https://image.tmdb.org/t/p/w1280' (string)
    'genre_ids',            # list of genre name which in genre_dict (list of string, e.g., ['판타지', '역사', '액션'])
    'original_language',    # e.g., 'ko' for Korean (string)
    'overview',             # movie overview or synopsis (string)
    'poster_path',          # concatenated with 'https://image.tmdb.org/t/p/w1280' (string)
    'release_date',         # release date in 'YYYY-MM-DD' format (string)
    'title',                # movie title in Korean (string)
    'vote_average',         # average rating (0-10 scale) (string with 2 decimal places)
    'vote_count'            # total number of votes (int)
    ]
    # Drop columns not in col_list
    df = df.drop(columns=[col for col in df.columns if col not in col_list])
    print(df)

    # Fill missing values and format columns
    base_url = "https://image.tmdb.org/t/p/w1280"
    df['backdrop_path'] = df['backdrop_path'].apply(
        lambda x: base_url + x if x else "/no_image.png"
    )
    df['genre_ids'] = df['genre_ids'].apply(
        lambda lst: [genre_dict.get(str(gid)) for gid in lst if str(gid) in genre_dict]
    )
    lang_map = {'ko': '한국어', 'en': '영어', 'ja': '일본어'}
    df['original_language'] = (df['original_language']
                            .fillna("N/A")
                            .map(lang_map)  # Map language codes to Korean names
    )
    df['overview'] = (df['overview']
                    .replace("", "줄거리가 없습니다.")
                    .fillna("줄거리가 없습니다.")
                    .apply(lambda x: x[:200] + "..." if len(x) > 200 else x))   # up to 200 characters
    df['poster_path'] = df['poster_path'].apply(
        lambda x: base_url + x if x else "/no_image.png"
    )
    df['release_date'] = df['release_date'].fillna("N/A")
    df['title'] = df['title'].replace("", "제목이 없습니다.").fillna("제목이 없습니다.")
    df['vote_average'] = df['vote_average'].apply(lambda x: f"{float(x):.2f}" if x else "N/A")
    df['vote_count'] = df['vote_count'].apply(lambda x: int(x) if x else "N/A")

    # Convert DataFrame to list of dictionaries
    movies = []
    for _, row in df.iterrows():
        movie = {
            "title": row['title'],
            "genre": ", ".join(row['genre_ids']),
            "rating": row['vote_average'],
            # "runtime": row.get('runtime', 'N/A'),  # runtime may not be in the original data
            "language": row['original_language'],
            "poster_url": row['poster_path'],
            "overview": row['overview']
        }
        movies.append(movie)
    return movies

def get_recommendations():
    if request.method == 'POST':
        genres      = request.form.getlist('genres')
        #adult       = request.form.get('adult')
        runtime     = request.form.get('runtime')
        min_rating  = float(request.form.get('min_rating'))
        languages   = request.form.getlist('languages')

        # example of recommended movies
        '''
        recommended_movies = [
        {
        "title": "기생충",
        "genre": "드라마, 스릴러",
        "rating": 8.6,
        "runtime": 132,
        "language": "ko",
        "poster_url": "https://www.themoviedb.org/t/p/w600_and_h900_bestv2/mSi0gskYpmf1FbXngM37s2HppXh.jpg",
        "overview": "가난한 가족이 부유한 가정에 들어가면서 벌어지는 이야기"
        },
        # ... more movies
        ]
        '''
        print(genres)   # ['28', '12']
        print(runtime)  # '1'
        print(min_rating)   # 5.0
        print(languages)    # ['ko', 'en']
        country=",".join(languages) if languages else 'ko'
        print(country)  # 'ko,en'
        recommended_movies = get_data(get_movies(
            api_key=TMDB_API_KEY,
            genre_id=",".join(genres) if genres else None,
            runtime_type= int(runtime) if runtime else 1,
            rating=min_rating if min_rating else 0,
            country=country
        ))

        return render_template(
                               'recommend_mv.html',
                               genres=genres,
                               runtime=runtime,
                               min_rating=min_rating,
                               languages=languages,
                               movies=recommended_movies
                               )
    else:
        return render_template('recommend_mv.html', movies=[])

if __name__ == "__main__":

    # for test
    while True:
        print(genre_dict)
        print()
        print("*"*100)
        input_lang = input("언어 입력 (ko, en, ja):>> ")
        input_runtime = input("영화 길이 범위 입력 (1: 1~2h, 2: 2~3h, 3: 3h 이상):>> ")
        input_genre = input("장르 번호 입력>> ")
        recommended_movies = get_movies(TMDB_API_KEY, genre_id=input_genre, runtime_type=int(input_runtime), rating=5, country=input_lang)

        rst = get_data(recommended_movies)
        print(rst[0])
        print("\n" + "*"*100)