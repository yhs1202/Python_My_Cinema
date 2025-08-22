Flask와 TMDb API, AWS Rekognition을 활용한 나만의 시네마 웹 애플리케이션입니다.

웹 UI에서 **배우 얼굴 찾기**, **영화추천**, **배우검색**, **미니게임, 영화제 정보**의 5가지 기능을 제공합니다.

A Flask-based mini web app that explores movies with TMDb API and face detection AWS Rekognition. It provides 5 main features via a web UI:

- Actor Face Detection
- Movie Recommendation
- Actor Search
- Mini Game
- Film Festival Information


## Features Overview

---

**1) 유명인(배우) 얼굴 찾기 (Actor Face Detection)**

- 업로드한 이미지에서 얼굴 탐지 및 유명인(배우) 인식 결과를 반환합니다.
- 주요 모듈: `aws.py` (Amazon Rekognition 호출)
- 출력 예시: 유명인 인식 결과 (이름, 성별, 직업, 생년월일, 출생지, Wikidata, IMDB, SNS Links, 소개) 및 최신 뉴스

**2) 영화추천 (Movie Recommendation)**

- TMDb **Discover / Recommendations** API 기반의 필터링/정렬로 추천 목록을 제공합니다.
- 주요 모듈: `recommend_movie.py` 여러 조건(장르, 언어, 상영시간, 개봉년도, 평점 등) 에 따라 영화 데이터 수집 및 가공, 화면 출력
- 출력 예시: 사용자가 설정한 조건을 바탕으로 검색된 영화들의 정보를 포스터와 함께 화면에 출력

**3) 배우검색 (Actor Search)**

- 배우명으로 검색하여 기본 프로필 및 대표작(필모그래피)을 보여줍니다.
- 주요 모듈: `search_actor.py`, `tmdb_helpers.py`

**4) 미니게임 (Mini Game)**

- TMDb 데이터로 간단한 퀴즈/맞히기 게임을 구성합니다.
- 주요 모듈: `movie_game_app.py`, `game_helpers.py`
- Game1: 포스터만 보고 개봉 순서로 맞추기 (1 to 9 Game)
- Game2: 감독 또는 배우 검색 후 관련된 작품 맞추기, 다 맞춘 후에는 상세 페이지로 로딩됩니다.

**5) 영화제 (Film Festival)**

- kobis 사이트를 통해 영화제 정보를 제공합니다.
- 주요 모듈: `festival_crawler`



## **Project Structure**

---

```
Python_My_Cinema/
├─ static/                  # CSS, JS, images
├─ templates/               # HTML templates
├─ .env.example             # Example of Local env_var (modify your API Key here)
├─ app.py                   # Main Flask app (routes/bootstrap)
├─ aws.py                   # AWS Rekognition helpers (face/celebrity detection)
├─ festival_crawler.py      # Scrapper for kobis (KOREA Box-office Information System)
├─ game_helpers.py          # Utilities for the movie quiz
├─ movie_game_app.py        # Standalone runner for the quiz game
├─ recommend_movie.py       # TMDb discovery/recommendation logic
├─ search_actor.py          # Actor/person search with TMDb
└─ tmdb_helpers.py          # Shared TMDb request helpers (params, mapping, utils)
```



## Run Application

---

**1) Requirements**

- Python 3.9+
- TMDb API Key
- AWS Access Key/Secret, Region

**2) Environment Variables**

Create a .env file in the root (see .env.example):

```
# TMDb
TMDB_API_KEY=your_tmdb_api_key
```

**3) Setup**

```bash
# 1) Clone
git clone https://github.com/yhs1202/Python_My_Cinema.git
cd Python_My_Cinema

# 2) (Recommended) Create & activate a venv
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3) Install deps
pip install -r requirements.txt
```

**4) Run Application**

```bash
python3 app.py
```


## **File Responsibilities & Dependencies**

---

**`app.py`**

- Flask 앱 생성, 라우팅, 템플릿 렌더링, 파일 업로드 처리 (main function)
- 기능 라우트에서 각 모듈 호출
(`tmdb_helpers.py`, `search_actor.py`, `aws.py`, `recommend_movie.py`, `movie_game_app.py`,  `game_helpers.py`, `festival_crawler.py`)
- **Dependencies**: Flask

**`tmdb_helpers.py`**

- `tmdb_get` 을 통한 TMDB API 요청 기능 수행
- API 응답을(배우 필모그래피 등) 표시용 데이터로 가공
- 이미지 분석부터 정보 조회까지 유명인 인식 기능의 전체 흐름 제어
- **Dependencies**: requests, Flask, werkzeug

**`search_actor.py`**

- 배우 검색(이름/출연작) 및 성별/나이/데뷔 연도 조건 필터링
- 필터링된 배우 검색 결과를 JSON 형식으로 반환 (`process_actor_search`)
- 특정 배우의 상세 정보를 HTML 페이지로 렌더링 (`get_actor_details`)
- **Dependencies**: Flask

**`aws.py`**

- Rekognition API 호출(예: `DetectFaces`, `RecognizeCelebrities`)
- 이미지 바이트 변환/전처리 후 결과를 웹 표시용 구조로 반환
- **Dependencies**: boto3, selenium, beautifulsoup

**`recommend_movie.py`**

- Discover/Recommendations 파라미터 구성: `with_genres`, `with_origin_country`, `with_runtime.gte/lte`, `language`, `sort_by`, `page` 등
- TMDb 결과를 DataFrame으로 정리 후 프론트 표시용 컬럼 가공
    - `overview` Truncates/cleans overview text
    - `poster_path`/`backdrop_path` -> 미존재 시 기본 이미지로 대체
- **Dependencies**: pandas, requests, flask

**`movie_game_app.py`**

- TMDB API 호출로 게임용 영화 목록 및 포스터 로드 (`get_popular_movies`)
- 퀴즈 게임의 메인 로직을 구현
- PyQt5를 사용하여 게임 UI를 구성하고 이벤트를 처리
- **Dependencies**: PyQt5, requests

**`game_helpers.py`**

- 두 가지 게임 모드(순서 맞추기, 진짜/가짜 찾기)의 백엔드 로직 처리
- 연령 등급 필터링(대체 호출 포함) 및 배우 국적 분석으로 게임 데이터 생성
- Flask 세션을 이용한 게임 정답 저장 및 관리
- **Dependencies**: Flask, python-dotenv

**`festival_crawler.py`**

- kobis 사이트에서 `get_film_festivals_with_selenium`을 사용해 크롤링
- **Dependencies**: selenium, webdriver-manager, beautifulsoup4


## TODO

---