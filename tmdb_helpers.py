# tmdb_helpers.py
import os
import requests
from flask import request, jsonify
from aws import recognize_celebrities
from werkzeug.utils import secure_filename
from typing import Optional, List, Dict, Any

# TMDB API 키와 기본 URL 설정
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
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

# 1. 파일이 업로드 됐는지 체크
def _normalize_to_rgb_jpeg(path: str) -> str:
    """업로드 이미지를 RGB JPEG로 정규화 (HEIC/CMYK 대비). 실패하면 원본 경로 반환."""
    try:
        from PIL import Image
        out_path = path + ".rgb.jpg"
        with Image.open(path) as im:
            if im.mode != "RGB":
                im = im.convert("RGB")
            # im.save(out_path, format="JPEG", quality=92)
        return out_path
    except Exception:
        # Pillow 미설치/변환 실패 시 원본 사용
        return path


def process_celeb_face():
    # 1) 업로드 체크
    if "file1" not in request.files:
        return jsonify({"result": "error", "message": "파일이 없습니다."}), 400

    file1 = request.files["file1"]
    if not file1 or file1.filename.strip() == "":
        return jsonify({"result": "error", "message": "파일 이름이 없습니다."}), 400

    # 2) 저장 + 정규화
    os.makedirs("static", exist_ok=True)
    file1_filename = secure_filename(file1.filename)
    save_path = os.path.join("static", file1_filename)
    # file1.save(save_path)
    save_path = _normalize_to_rgb_jpeg(save_path)  # 실패 시 원본 경로 반환

    # 3) AWS Rekognition 유명인 인식
    try:
        celeb_info_from_aws = recognize_celebrities(save_path)
    except Exception as e:
        return jsonify({"result": "error", "message": f"recognize_celebrities crashed: {e}"}), 500

    if not isinstance(celeb_info_from_aws, dict):
        return jsonify({"result": "error", "message": "AWS returned non-dict response"}), 502

    if celeb_info_from_aws.get("result") != "success":
        # "empty" 또는 "error"면 그대로 클라이언트에 알림
        return jsonify(celeb_info_from_aws), 200

    # 4) TMDB 상세 + 외부ID + 필모그래피(영화/TV 표) 구성
    celebrities_with_details = []
    for celeb in celeb_info_from_aws.get("celebrities", []):
        name = celeb.get("name")
        person_id, _ = tmdb_search_person_id(name) if name else (None, None)

        if person_id:
            details = tmdb_person_details(person_id)
            external_ids = tmdb_person_external_ids(person_id)

            # 필모그래피: 영화/TV 크레딧 → 표 데이터
            movie_credits = tmdb_person_movie_credits(person_id)
            tv_credits = tmdb_person_tv_credits(person_id)
            movie_table = build_movie_table(movie_credits)  # 평점 desc, 인기도 desc 정렬됨
            tv_table = build_tv_table(tv_credits)

            celeb.update({
                "birthday": details.get("birthday") or "정보 없음",
                "place_of_birth": details.get("place_of_birth") or "정보 없음",
                "known_for_department": details.get("known_for_department") or "정보 없음",
                "biography": details.get("biography") or "",
                "external_ids": external_ids or {},
                "filmography": {
                    "movies": movie_table, 
                    "tv": tv_table           
                }
            })
        else:
            celeb.update({
                "birthday": "정보 없음",
                "place_of_birth": "정보 없음",
                "known_for_department": "정보 없음",
                "biography": "",
                "external_ids": {},
                "filmography": {"movies": [], "tv": []}
            })

        celebrities_with_details.append(celeb)

    # 5) 최종 응답
    return jsonify({
        "result": "success",
        "count": len(celebrities_with_details),
        "celebrities": celebrities_with_details
    }), 200


# 배우의 필모그래피 데이터 받아오기
# --- TMDB 크레딧 호출 ---
def tmdb_person_movie_credits(person_id: int):
    # 출연/제작 모두 오지만 여기서는 cast 위주 사용
    return tmdb_get(f"/person/{person_id}/movie_credits", language="ko-KR")

def tmdb_person_tv_credits(person_id: int):
    return tmdb_get(f"/person/{person_id}/tv_credits", language="ko-KR")

def _role_type_movie(order: Optional[int]) -> str:
    if order is None:
        return "조연"
    if order <= 2:
        return "주연"
    if order <= 6:
        return "조연"
    return "특별출연"

def _role_type_tv(order: Optional[int], ep_count: Optional[int]) -> str:
    if ep_count is not None and ep_count <= 2:
        return "특별출연"
    if order is not None and order <= 2:
        return "주연"
    return "조연"


IMG_BASE = "https://image.tmdb.org/t/p/w154"

def _year(date_str: Optional[str]) -> str:
    return (date_str or "")[:4] or "-"

def _sort_key(item):
    # vote_average desc, popularity desc
    return (-float(item.get("vote", 0) or 0), -float(item.get("popularity", 0) or 0))

def build_movie_table(movie_credits: dict) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for m in (movie_credits or {}).get("cast", []):
        rows.append({
            "title": m.get("title") or m.get("original_title") or "",
            "year": _year(m.get("release_date")),
            "vote": m.get("vote_average") or 0,
            "popularity": m.get("popularity") or 0,
            "character": m.get("character") or "",
            "role_type": _role_type_movie(m.get("order")),
            "poster": (IMG_BASE + m["poster_path"]) if m.get("poster_path") else None,
            "tmdb_id": m.get("id"),
        })
    rows.sort(key=_sort_key)
    return rows


def build_tv_table(tv_credits: dict) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for t in (tv_credits or {}).get("cast", []):
        rows.append({
            "title": t.get("name") or t.get("original_name") or "",
            "year": _year(t.get("first_air_date")),
            "vote": t.get("vote_average") or 0,
            "popularity": t.get("popularity") or 0,
            "character": t.get("character") or "",
            "role_type": _role_type_tv(t.get("order"), t.get("episode_count")),
            "poster": (IMG_BASE + t["poster_path"]) if t.get("poster_path") else None,
            "tmdb_id": t.get("id"),
            "episode_count": t.get("episode_count"),
        })
    rows.sort(key=_sort_key)
    return rows

def tmdb_person_combined_credits(person_id: int):
    """TMDB에서 인물의 영화와 TV 출연작 전체 목록을 가져오는 함수"""
    data = tmdb_get(f"/person/{person_id}/combined_credits", language="ko-KR")
    return data.get("cast", [])
