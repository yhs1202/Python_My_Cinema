# tmdb_helpers.py

import os
import requests

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
