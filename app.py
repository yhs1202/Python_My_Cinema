
# -*- coding: utf-8 -*-
## 2) app.py (업데이트: /filmography_by_name 추가, DataFrame 로직 반영)

# 임포트 & 기본 세팅
import os
import boto3 #boto3로 AWS Rekognition(유명인 인식) 클라이언트용. 현재 코드 조각에서는 실제 호출은 안함(다른 라우트에서 씀)
import requests #requests로 TMDB REST API 호출, pandas로 표 정리(정렬, 중복제거)
import pandas as pd  #표로 정리

from flask import Flask, render_template, request, jsonify 
# Flask : 파이썬으로 웹서버를 만듣는 "앱 본체" 클래스
# Render_template : Templates / 폴더의 HTML 파일을 화면에 띄울 때 사용
# request : 브라우저가 보낸 입력값을 읽을 때 사용(폼 데이터, 파일 업로드, JSON 등)
# jsonfy : 파이썬 dick/list -> JSOM 응답으로 바꿔보내기

from flask import redirect          # 페이지 이동
from flask import make_response     # 페이지 이동 시 정보 유지

from aws import recognize_celebrities
# from flask import redirect 다른 URL로 페이지 이동시킬 때 사용

from werkzeug.utils import secure_filename

# Ensure the static directory exists
if not os.path.exists("static"):
    os.mkdir("static")

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "<YOUR_TMDB_API_KEY>")
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))

# root page
@app.route("/")
def index():
    return render_template("pj_prac.html")

# AWS 자격증명은 표준 방식으로 설정되어 있어야 합니다.
rekognition = boto3.client("rekognition", region_name=AWS_REGION)
BASE = "https://api.themoviedb.org/3"

# ---------------- TMDB helpers ----------------

def tmdb_get(path, **params):
    params.setdefault("api_key", TMDB_API_KEY)
    params.setdefault("language", "ko-KR")
    r = requests.get(f"{BASE}{path}", params=params, timeout=10)
    r.raise_for_status()
    return r.json()

#공통 GET함수. 기본적으로 헌국어와 API 키를 붙여 호출

def tmdb_search_person_id(name: str):
    data = tmdb_get("/search/person", query=name)
    results = data.get("results", [])
    if not results:
        return None, None
    person = results[0]
    return person.get("id"), person

# 이름으로 사람을 검색 -> 가장 첫 결과의 ID와 원본 객체를 반환

def tmdb_combined_credits(person_id: int):
    data = tmdb_get(f"/person/{person_id}/combined_credits")
    return data.get("cast", [])

#그 인물의 영화 + TV합본 출연 목록을 Cast로 가져옴

# 출연유형 간이 규칙

def role_type_from_order(order):
    try:
        o = int(order)
    except Exception:
        return ""
    if o <= 2:
        return "주연"
    if o <= 10:
        return "조연"
    return "특별출연"
# TMDB의 order(출연 크레딧 순서)가 작을수록 비중이 큰 역할이라는 가정으로 주연/조연/특별출연 분류
# DataFrame → 영화/TV dict 리스트 변환 (사용자 제공 로직 반영)

def build_tables_from_cast(cast): #필모그래피 -> 표 데이터만들기, TMDB cast JSON을 표(데이터프레임)로 변환. 연도는 YYYY만 추출
    if not cast:
        return [], []

    df_all = pd.DataFrame([{
        "매체":  f.get("media_type"),
        "제목":  f.get("title") or f.get("name"),
        "연도":  (f.get("release_date") or f.get("first_air_date") or "")[:4],
        "역할":  f.get("character"),
        "평점":  f.get("vote_average"),
        "인기":  f.get("popularity"),
        "order": f.get("order")
    } for f in cast])

    if df_all.empty:
        return [], []

    df_all["연도"] = df_all["연도"].fillna("")
    df_all = df_all.drop_duplicates(subset=["매체", "제목", "연도"])  
    # 연도 결측 보정 매체, 제목, 연도 기준 중복 제거

    movies = df_all[df_all["매체"] == "movie"].copy()
    tvs    = df_all[df_all["매체"] == "tv"].copy()

    # 정렬: 평점 ↓, 인기 ↓, 연도 ↓
    for d in (movies, tvs):
        d["평점"] = pd.to_numeric(d["평점"], errors="coerce")
        d["인기"] = pd.to_numeric(d["인기"], errors="coerce")
        d.sort_values(["평점", "인기", "연도"], ascending=[False, False, False], inplace=True)
        d.reset_index(drop=True, inplace=True)
        d.index += 1
    # 영화/TV 숫자형으로 캐스팅 후 평점(내림차순), 인기(내림차순), 연도(내림차순) 순으로 보기좋게 정렬

    # 출연유형 계산
    def to_rows(df):
        rows = []
        for _, r in df.iterrows():
            rows.append({
                "title": r["제목"],
                "year": r["연도"],
                "character": r["역할"],
                "vote_average": r["평점"],
                "role_type": role_type_from_order(r.get("order"))
            })
        return rows

    return to_rows(movies.head(50)), to_rows(tvs.head(50))
