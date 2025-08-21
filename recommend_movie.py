# recommend_movie.py
import pandas as pd
from flask import render_template, request
from tmdb_helpers import tmdb_get
import random


def build_release_date_filter(year_type: int) -> dict:
    """
    TMDb API VALUE 생성 위한 개봉 날짜 범위 생성 함수 (dict)
    year_type:
      1: all
      2: before 2000
      3: 2000-2010
      4: 2010-2020
      5: after 2020
    """
    f = {}
    if year_type == 0:  # all
        return f
    elif year_type == 1:  # before 2000
        f["primary_release_date.lte"] = "1999-12-31"
    elif year_type == 2:  # 2000-2010
        f["primary_release_date.gte"] = "2000-01-01"
        f["primary_release_date.lte"] = "2010-12-31"
    elif year_type == 3:  # 2010-2020
        f["primary_release_date.gte"] = "2010-01-01"
        f["primary_release_date.lte"] = "2020-12-31"
    elif year_type == 4:  # 2021-
        f["primary_release_date.gte"] = "2021-01-01"
    else:
        pass
    return f


def build_params(genre_id=None, runtime_type=None, release_year_type=0, rating=None, country='ko') -> dict:
    """
    TMDB API 호출에 필요한 파라미터를 생성하는 함수
    :param genre_id: 장르 ID (e.g., '28,12' for 액션, 모험)
    :param runtime_type: 1(60-120), 2(120-180), 3(180+)
    :param year_type: 1(all), 2(before 2000), 3(2000-2010), 4(2010-2020), 5(after 2020)
    :param rating: 최소 평점 (0-10)
    :param country: ISO 639-1 국가 코드 (e.g., 'ko', 'en', 'ja')
    """
    params = {
        "with_genres": genre_id,
        "with_runtime.gte": 60 * runtime_type,  # 최소 상영 시간
        "with_runtime.lte": 60 * (runtime_type + 1) if runtime_type != 3 else None,  # 최대 상영 시간
        **build_release_date_filter(release_year_type),  # 개봉 날짜 필터
        "vote_average.gte": rating,  # 최소 평점
        "with_original_language": country,  # 국가 코드로 필터링
        "language": "ko-KR",  # 한국어 데이터 요청
        "sort_by": "popularity.desc",
        "include_adult": False,
        "certification_country": "KR",  # 한국 등급 필터링
        "certification.lte": "15"  # 한국 등급 중 ALL/12/15까지만 포함
    }
    return params

def get_movies(genre_id=None, genre_or=False, runtime_type=None, release_year_type_list=[0], rating=None, country='ko') -> pd.DataFrame:
    """
    설정한 조건의 영화 목록을 페이지 범위로 가져오는 함수
    """

    #### Modify page range here ####
    page_range = 5

    all_movies = []
    ###################
    seen_ids = set() # 중복 방지용 변수 설정
    ###################
    # multiple countries processing
    countries = country.split(",") if country else ['ko']
    # if all year types are selected,
    # build_release_date_filter will return empty dict (No constraints)
    if len(release_year_type_list) == 4:    
        release_year_type_list = [0]

    # genre_id AND OR Logic
    genre_id = genre_id.replace(",", "|") if genre_or else genre_id

    for release_year_type in release_year_type_list:
        for country in countries:
            for page_num in range(1, page_range + 1):    
                params = build_params(
                    genre_id=genre_id,
                    runtime_type=runtime_type,
                    release_year_type=release_year_type,
                    rating=rating,
                    country=country
                ) 
                movies_data = tmdb_get('/discover/movie', **params)
                movies = movies_data.get('results', [])
                if not movies:
                    print(f"{page_num} 페이지에서 영화를 찾을 수 없습니다.")
                    break
                # 중복 제거 : id 기준으로 중복되는 것 제거
                for m in movies:
                    mid = m.get('id')
                    if mid is None:
                        continue
                    if mid not in seen_ids:
                        seen_ids.add(mid)
                        all_movies.append(m)
    # 예비 중복 방지 코드 : 혹시 중복이 섞이더라도 id 기준으로 한번 더 고유화
    unique_by_id = {}
    for m in all_movies:
        unique_by_id[m['id']] = m
    all_movies = list(unique_by_id.values())

    #
    if len(all_movies) > 21:
        all_movies = random.sample(all_movies, 21)
    
    return pd.DataFrame(all_movies)


def get_data(df: pd.DataFrame)-> list:
    """
    DataFrame에서 필요한 컬럼을 추출하고, 형식을 맞춰서 영화 정보를 반환하는 함수
    """
    col_list = [
    'backdrop_path',        # concatenated with 'https://image.tmdb.org/t/p/w1280' (string)
    'genre_ids',            # list of genre name which in genre_dict (list of string, e.g., ['판타지', '역사', '액션'])
    'original_language',    # e.g., 'ko' for Korean (string)
    'overview',             # movie overview or synopsis (string)
    'poster_path',          # concatenated with 'https://image.tmdb.org/t/p/w1280' (string)
    'release_date',         # release date in 'YYYY-MM-DD' format (string)
    'title',                # movie title in Korean (string)
    'vote_average',         # average rating (0-10 scale) (string with 2 decimal places)
    'vote_count',           # total number of votes (int)
    'id'                    # movie ID (numpy.int64)
    ]
    # Drop columns not in col_list
    df = df.drop(columns=[col for col in df.columns if col not in col_list])
    # print(df)

    ## Fill missing values and format columns
    # Concatenate base URL for backdrop_path
    base_url = "https://image.tmdb.org/t/p/w1280"
    df['backdrop_path'] = df['backdrop_path'].apply(
        lambda x: base_url + x if x else "/no_image.png"
    )
    # Map genre IDs to names using genre_dict
    genre_dict = {
    "28": "액션", "12": "모험", "16": "애니메이션", "35": "코미디",
    "80": "범죄", "99": "다큐멘터리", "18": "드라마", "10751": "가족",
    "27": "공포", "10749": "로맨스", "878": "SF", "53": "스릴러",
    "10752": "전쟁", "37": "서부", "14": "판타지", "36": "역사",
    "10402": "음악", "9648": "미스터리"
    }
    df['genre_ids'] = df['genre_ids'].apply(
        lambda lst: [genre_dict.get(str(gid)) for gid in lst if str(gid) in genre_dict]
    )
    # Map original_language codes to Korean names
    lang_map = {'ko': '한국어', 'en': '영어', 'ja': '일본어'}
    df['original_language'] = (df['original_language']
                            .fillna("N/A")
                            .map(lang_map)
    )
    # Fill overview with default text if empty or NaN
    df['overview'] = (df['overview']
                    .replace("", "줄거리가 없습니다.")
                    .fillna("줄거리가 없습니다.")
                    .apply(lambda x: x[:200] + "..." if len(x) > 200 else x))   # up to 200 characters
    # Concatenate base URL for poster_path
    df['poster_path'] = df['poster_path'].apply(
        lambda x: base_url + x if x else "/no_image.png"
    )
    # Format release_date to 'YYYY-MM-DD' or 'N/A'
    df['release_date'] = df['release_date'].fillna("N/A")
    # Format title, vote_average, and vote_count
    df['title'] = df['title'].replace("", "제목이 없습니다.").fillna("제목이 없습니다.")
    df['vote_average'] = df['vote_average'].apply(lambda x: f"{float(x):.2f}" if x else "N/A")
    df['vote_count'] = df['vote_count'].apply(lambda x: int(x) if x else "N/A")
    # Convert id to string and add TMDB URL
    df['id'] = 'https://www.themoviedb.org/movie/' + df['id'].astype(str)

    # Convert DataFrame to list of dictionaries
    movies = []
    for _, row in df.iterrows():
        movie = {
            "id": row['id'],
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
    """
    Flask route to handle movie recommendations based on user input
    """
    if request.method == 'POST':
        genres      = request.form.getlist('genres')
        genre_or    = request.form.get('genre_or')
        # adult       = request.form.get('adult')
        runtime     = request.form.get('runtime')
        year_types  = request.form.getlist('release_year_range')
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
        print(year_types)   # '1,2,3'
        print(min_rating)   # 5.0
        print(languages)    # ['ko', 'en']
        # Get recommended movies based on the selected criteria
        try:
            recommended_movies = get_data(get_movies(
                genre_id        = ",".join(genres) if genres else None,
                genre_or        = True if genre_or == 'on' else False,
                runtime_type    = int(runtime) if runtime else 1,
                release_year_type_list = [int(x) for x in year_types] if year_types else [0],
                rating          = min_rating if min_rating else 0,
                country         = ",".join(languages) if languages else 'ko'
            ))
            return render_template('recommend_mv.html',
                                genres=genres,
                                runtime=runtime,
                                min_rating=min_rating,
                                languages=languages,
                                movies=recommended_movies
                                )
        except Exception as e:
            print(f"!!!!!!!!!!!!!!Error occurred while fetching movies: {e}")
            return render_template('recommend_mv_fail.html',
                    warning="조건에 맞는 영화가 없습니다 ㅠㅠ 다시 시도해 주세요.")
    else:
        return render_template('recommend_mv.html', movies=[])


if __name__ == "__main__":
    # for test
    # while True:
    #     print(genre_dict)
    #     print()
    #     print("*"*100)
    #     input_lang = input("언어 입력 (ko, en, ja):>> ")
    #     input_runtime = input("영화 길이 범위 입력 (1: 1~2h, 2: 2~3h, 3: 3h 이상):>> ")
    #     input_genre = input("장르 번호 입력>> ")
    #     recommended_movies = get_movies(genre_id=input_genre, runtime_type=int(input_runtime), rating=5, country=input_lang)
    #     recommended_movies = get_data(recommended_movies)
    pass