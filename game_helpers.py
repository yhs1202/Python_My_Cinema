import os
import random
from collections import Counter
from dotenv import load_dotenv
from flask import jsonify, request, session
from tmdb_helpers import tmdb_get

load_dotenv()

def get_popular_movies(page=None, country_code=None):
    """
    TMDB API로 인기 영화 목록을 가져오는 함수.
    대한민국 등급 기준 '청소년 관람불가' 영화를 제외합니다.
    """
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        print("오류: TMDB_API_KEY가 설정되지 않았습니다.")
        return None

    request_page = page if page else random.randint(1, 10)

    params = {
        "api_key": api_key,
        "language": "ko-KR",
        "sort_by": "popularity.desc",
        "page": request_page,
        "include_adult": "false",
        "certification_country": "KR",
        "certification.lte": "15"
    }
    if country_code:
        params.setdefault("with_origin_country", country_code)

    data = tmdb_get('/discover/movie', **params).get('results', [])
        
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
    
    if len(movies) < 9:
        print(f"경고: 연령 등급 필터링 결과가 부족하여, 필터 없이 다시 요청합니다.")
        params.pop("certification_country", None)
        params.pop("certification.lte", None)
        data_fallback = tmdb_get('/discover/movie', **params).get('results', [])
        
        existing_ids = {m['id'] for m in movies}
        for movie in data_fallback:
            if len(movies) >= 9: break
            if movie.get('poster_path') and movie.get('release_date') and movie['id'] not in existing_ids:
                movies.append({ 'id': movie['id'], 'title': movie['title'], 'poster_path': movie['poster_path'], 'release_date': movie['release_date'] })

    return movies


def search_person(name):
    """이름으로 배우/감독 검색"""
    api_key = os.getenv("TMDB_API_KEY")
    params = {
        "api_key": api_key,
        "language": "ko-KR",
        "query": name
    }
    results = tmdb_get("/search/person", **params)["results"]
    
    return results[0]['id'] if results else None


def get_person_details(person_id):
    """사람 ID로 상세 정보(주요 분야 포함)와 영화 목록 전체를 반환합니다."""
    api_key = os.getenv("TMDB_API_KEY")
    
    params = {
        "api_key": api_key,
        "language": "ko-KR",
        "append_to_response": "movie_credits"
    }

    return tmdb_get(f"/person/{person_id}", **params)


def get_country_from_movies(movie_ids):
    """다수의 영화 ID를 받아 가장 빈도가 높은 제작 국가 코드를 찾아냅니다."""
    api_key = os.getenv("TMDB_API_KEY")
    countries = []
    for movie_id in movie_ids[:5]:
        params = {
            "api_key": api_key,
            "language": "ko-KR"
        }
        data = tmdb_get(f"/movie/{movie_id}", **params)
        if data.get('production_countries'):
            countries.append(data['production_countries'][0]['iso_3166_1'])
            
    return Counter(countries).most_common(1)[0][0] if countries else None

def get_detailed_movie_list(movies):
    """기본 영화 정보 목록을 받아, 각 영화의 상세 정보를 TMDB에서 가져와 반환합니다."""
    api_key = os.getenv("TMDB_API_KEY")
    detailed_movies = []
    for movie in movies:
        movie_id = movie.get('id')
        if not movie_id or not api_key: 
            continue
        params = {
            "api_key": api_key,
            "language": "ko-KR",
            "append_to_response": "credits"
        }
        data = tmdb_get(f"/movie/{movie_id}", **params)
        director = next((crew['name'] for crew in data.get('credits', {}).get('crew', []) if crew['job'] == 'Director'), "정보 없음")
        cast = [actor['name'] for actor in data.get('credits', {}).get('cast', [])[:3]]
        genres = [genre['name'] for genre in data.get('genres', [])]
        detailed_movies.append({'title': data.get('title'),'poster_path': data.get('poster_path'),'release_date': data.get('release_date'),'overview': data.get('overview', '줄거리 정보가 없습니다.')[:100] + "...",'vote_average': round(data.get('vote_average', 0), 1),'director': director,'cast': cast,'genres': genres})

    return detailed_movies

# --- 요청 처리 함수 ---

def process_game_movies():
    """Mode 1 요청 처리 및 세션에 정답 저장"""
    movies = get_popular_movies()
    if movies:
        correct_answers = sorted(movies, key=lambda x: x['release_date'])
        session['correct_answers'] = correct_answers
        return jsonify({"result": "success", "movies": movies})
    else:
        return jsonify({"result": "error", "message": "Failed to load movies"}), 500

def process_person_game_request(name, real_count=5):
    """Mode 2 요청 처리 (배우/감독 역할 구분 로직 적용)"""
    person_id = search_person(name)
    if not person_id:
        return jsonify({"result": "error", "message": f"'{name}'을(를) 찾을 수 없습니다."}), 404

    person_data = get_person_details(person_id)
    if not person_data:
        return jsonify({"result": "error", "message": f"'{name}'의 상세 정보를 가져올 수 없습니다."}), 404
    
    department = person_data.get('known_for_department')
    movie_credits = person_data.get('movie_credits', {})
    
    # 최종적으로 사용할 정답 후보 영화 목록
    final_movie_list = []

    if department == 'Acting':
        print(f"'{name}'은(는) 배우입니다. 출연작을 우선으로 검색합니다.")
        final_movie_list = movie_credits.get('cast', [])
    elif department == 'Directing':
        print(f"'{name}'은(는) 감독입니다. 연출작을 우선으로 검색합니다.")
        final_movie_list = [m for m in movie_credits.get('crew', []) if m.get('job') == 'Director']
    else:
        print(f"'{name}'의 주요 분야({department})에 따라 전체 참여작을 검색합니다.")
        final_movie_list = movie_credits.get('cast', []) + movie_credits.get('crew', [])

    if not final_movie_list:
        return jsonify({"result": "error", "message": f"'{name}'의 대표 영화 정보를 찾을 수 없습니다."}), 404
        
    movie_ids_from_person = [credit['id'] for credit in final_movie_list if credit.get('id')]
    origin_country = get_country_from_movies(movie_ids_from_person)

    unique_real_movies = list({movie['id']: movie for movie in final_movie_list if movie.get('poster_path')}.values())
    random.shuffle(unique_real_movies)
    real_answers = unique_real_movies[:real_count]
    for movie in real_answers:
        movie['is_real'] = True
    
    session['correct_answers'] = real_answers

    fake_count = 9 - len(real_answers)
    if fake_count > 0:
        fake_movies = get_popular_movies(page=random.randint(1, 10), country_code=origin_country)
        real_movie_ids = {m['id'] for m in real_answers}
        fake_movies_filtered = [m for m in fake_movies if m['id'] not in real_movie_ids] if fake_movies else []
        for movie in fake_movies_filtered:
            movie['is_real'] = False
        game_list = real_answers + fake_movies_filtered[:fake_count]
    else:
        game_list = real_answers[:9]

    random.shuffle(game_list)
    return jsonify({"result": "success", "movies": game_list, "person_name": name, "real_movie_count": len(real_answers)})

def handle_person_game_request():
    """Mode 2 웹 요청 처리"""
    person_name = request.args.get('name')
    if not person_name:
        return jsonify({"result": "error", "message": "이름을 입력해주세요."}), 400
    return process_person_game_request(person_name)