# search_actor.py

from flask import request, jsonify, render_template
from datetime import datetime
from tmdb_helpers import tmdb_get, tmdb_person_details, tmdb_person_combined_credits, tmdb_person_external_ids

# --- Helper Functions ---

def _calculate_age(birthdate_str):
    """생년월일 문자열로부터 나이를 계산하는 헬퍼 함수"""
    if not birthdate_str:
        return None
    try:
        birthdate = datetime.strptime(birthdate_str, "%Y-%m-%d")
        today = datetime.today()
        return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    except (ValueError, TypeError):
        return None

# --- Core Logic ---

def search_and_filter_actors(name, gender, age_range, debut_year_range, genre_id):
    """배우 검색 및 서버 사이드 필터링을 수행하는 메인 함수"""
    
    initial_actors = {} 

    if name:
        results = tmdb_get("/search/person", query=name, language="ko-KR").get("results", [])
        for person in results:
            if person.get("id"):
                initial_actors[person["id"]] = person
    else:
        discover_params = {
            "language": "ko-KR",
            "sort_by": "popularity.desc",
            "with_genres": genre_id if genre_id else ""
        }
        for page in range(1, 3):
            discover_params["page"] = page
            movies = tmdb_get("/discover/movie", **discover_params).get("results", [])
            for movie in movies:
                movie_id = movie.get("id")
                if not movie_id: continue
                
                credits = tmdb_get(f"/movie/{movie_id}/credits").get("cast", [])
                for person in credits[:5]:
                    if person.get("id") and person["id"] not in initial_actors:
                        initial_actors[person["id"]] = person

    filtered_actors = []
    
    for person in initial_actors.values():
        if len(filtered_actors) >= 20:
            break

        person_id = person.get("id")
        if not person_id: continue
            
        details = tmdb_person_details(person_id)
        
        if gender and details.get("gender") != int(gender):
            continue
        
        if age_range:
            age = _calculate_age(details.get("birthday"))
            if age is None: continue
            
            if age_range == "10s" and not (10 <= age < 20): continue
            if age_range == "20s" and not (20 <= age < 30): continue
            if age_range == "30s" and not (30 <= age < 40): continue
            if age_range == "40s" and not (40 <= age < 50): continue
            if age_range == "50s_over" and not (age >= 50): continue

        if debut_year_range:
            credits = tmdb_person_combined_credits(person_id)
            if not credits: continue

            valid_credits = [c for c in credits if c.get("release_date") or c.get("first_air_date")]
            if not valid_credits: continue

            valid_credits.sort(key=lambda x: x.get("release_date") or x.get("first_air_date"))
            first_work_date = valid_credits[0].get("release_date") or valid_credits[0].get("first_air_date")
            
            if not first_work_date or len(first_work_date) < 4: continue
            
            first_work_year = int(first_work_date[:4])

            if debut_year_range == "2020s" and not (2020 <= first_work_year <= 2029): continue
            if debut_year_range == "2010s" and not (2010 <= first_work_year <= 2019): continue
            if debut_year_range == "2000s" and not (2000 <= first_work_year <= 2009): continue
            if debut_year_range == "1990s" and not (1990 <= first_work_year <= 1999): continue
            if debut_year_range == "pre_1990s" and not (first_work_year < 1990): continue
        
        filtered_actors.append({
            "id": person.get("id"),
            "name": person.get("name"),
            "profile_path": person.get("profile_path"),
            "known_for_department": details.get("known_for_department", "N/A")
        })

    return filtered_actors

# --- Request Handlers ---

def process_actor_search():
    """Request로부터 필터 값을 가져와 검색을 처리하는 총괄 함수"""
    name = request.args.get("name", "")
    gender = request.args.get("gender", "")
    age_range = request.args.get("age", "")
    debut_year = request.args.get("debut", "")
    genre = request.args.get("genre", "")

    actors = search_and_filter_actors(name, gender, age_range, debut_year, genre)
    
    return jsonify(actors)

def get_actor_details(actor_id):
    """배우 상세 정보 페이지를 위한 데이터를 처리하고 렌더링합니다."""
    
    details = tmdb_person_details(actor_id)
    credits = tmdb_person_combined_credits(actor_id)
    external_ids = tmdb_person_external_ids(actor_id)

    valid_credits = [c for c in credits if c.get("release_date") or c.get("first_air_date")]
    sorted_credits = sorted(
        valid_credits, 
        key=lambda x: x.get("release_date") or x.get("first_air_date"), 
        reverse=True
    )

    actor_data = {
        "details": details,
        "credits": sorted_credits[:20],
        "external_ids": external_ids
    }
    
    return render_template("actor_detail.html", actor=actor_data)
