# tmdb_helpers.py

import os
import requests
from flask import Flask, render_template, request, jsonify
from aws import recognize_celebrities
from werkzeug.utils import secure_filename




# TMDB API 키와 기본 URL 설정
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "47f87bbcaf0d3e659a0bcbdf66f536d0")
BASE = "https://api.themoviedb.org/3"

def tmdb_get(path, **params):
    """TMDB API 요청을 위한 기본 함수"""
    params.setdefault("api_key", TMDB_API_KEY)
    try:
        r = requests.get(f"{BASE}{path}", params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        print(f"TMDB API 요청 실패: {e}")
        return {}

def tmdb_search_person_id(name: str):
    """이름으로 TMDB에서 인물 ID를 검색하는 함수"""
    data = tmdb_get("/search/person", query=name, language="ko-KR")
    results = data.get("results", [])
    if not results:
        return None, None
    person = results[0]
    return person.get("id"), person

def tmdb_person_details(person_id: int):
    """
    TMDB에서 배우의 상세 정보를 가져오는 함수.
    한국어 소개가 없으면 영어 소개를 대신 가져옵니다.
    """
    details_ko = tmdb_get(f"/person/{person_id}", language="ko-KR")
    if details_ko and not details_ko.get('biography'):
        details_en = tmdb_get(f"/person/{person_id}")
        if details_en and details_en.get('biography'):
            details_ko['biography'] = details_en['biography']
    return details_ko

# ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
# 배우의 소셜 미디어 ID (인스타그램, 트위터 등)를 가져오는 함수를 새로 추가합니다.
def tmdb_person_external_ids(person_id: int):
    """TMDB에서 인물의 External ID를 가져오는 함수"""
    return tmdb_get(f"/person/{person_id}/external_ids")
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲



# 배우의 영화 및 TV프로그램 필모그래피를 나타내주는 코드
def tmdb_person_combined_credits(person_id: int):
    """영화+TV 합본 크레딧"""
    data = tmdb_get(f"/person/{person_id}/combined_credits", language="ko-KR")
    return data.get("cast", [])

def _role_type_from_order(order):
    try:
        o = int(order)
    except Exception:
        return ""
    if o <= 2:  return "주연"
    if o <= 10: return "조연"
    return "특별출연"

def build_filmography_tables(person_id: int, sort_by: str = "rating"):
    """
    반환: movies, tvs  (각각 [{title, year, character, role_type, vote_average}, ...])
    sort_by: "rating"(기본) 또는 "year"
    """
    cast = tmdb_person_combined_credits(person_id)

    def _to_year(s):
        if not s: return None
        try: return int(s[:4])
        except: return None

    movies, tvs = [], []
    seen_m, seen_t = set(), set()

# 배우의 영화 및 TV프로그램 필모그래피를 나타내주는 코드






def process_celeb_face():
    if "file1" not in request.files:
        return jsonify({"error": "파일이 없습니다."}), 400

    file1 = request.files["file1"]
    if file1.filename == "":
        return jsonify({"error": "파일 이름이 없습니다."}), 400

    file1_filename = secure_filename(file1.filename)
    save_path = os.path.join("static", file1_filename)
    file1.save(save_path)

    celeb_info_from_aws = recognize_celebrities(save_path)
    
    if celeb_info_from_aws.get("result") != "success":
        return jsonify(celeb_info_from_aws)

    celebrities_with_details = []
    for celeb in celeb_info_from_aws.get("celebrities", []):
        person_id, _ = tmdb_search_person_id(celeb['name'])
        
        if person_id:
            details = tmdb_person_details(person_id)
            # ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
            # 소셜 미디어 ID를 가져오는 로직을 추가합니다.
            external_ids = tmdb_person_external_ids(person_id)
            # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
            
            celeb['birthday'] = details.get('birthday', '정보 없음')
            celeb['place_of_birth'] = details.get('place_of_birth', '정보 없음')
            celeb['known_for_department'] = details.get('known_for_department', '정보 없음')
            celeb['biography'] = details.get('biography', '')
            # ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
            # 가져온 소셜 미디어 ID를 결과에 추가합니다.
            celeb['external_ids'] = external_ids
            # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
        else:
            celeb['birthday'] = '정보 없음'
            celeb['place_of_birth'] = '정보 없음'
            celeb['known_for_department'] = '정보 없음'
            celeb['biography'] = ''
            celeb['external_ids'] = {} # ID가 없을 경우 빈 딕셔너리 전달
            
        celebrities_with_details.append(celeb)

    celeb_info_from_aws['celebrities'] = celebrities_with_details
    
    return jsonify(celeb_info_from_aws)