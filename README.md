# Python_My_Cinema
---
Flask와 TMDb API, AWS Rekognition을 활용한 나만의 시네마 웹 애플리케이션입니다.  
웹 UI에서 **얼굴찾기**, **영화추천**, **배우검색**, **미니게임**의 4가지 기능을 제공합니다.

A Flask web application that integrates the TMDb API and optionally AWS Rekognition.
It provides 4 main features via a web UI:
- Face Detection
- Movie Recommendation
- Actor Search
- Mini Game

![0](/static/readme_img/0_main_example.png)

---

## Features Overview

### 1) 얼굴찾기 (Face Detection)
- 업로드한 이미지에서 얼굴 탐지 및 유명인 인식 결과를 반환합니다.
- 주요 모듈: `aws.py` (Amazon Rekognition 호출)
- 출력 예시: 유명인 인식 결과 (이름, 성별, 직업, 생년월일, 출생지, Wikidata, IMDB, SNS Links, 소개) 및 최신 뉴스

![1](/static/readme_img/1_face_detection_example.png)

### 2) 영화추천 (Movie Recommendation)
- TMDb **Discover / Recommendations** API 기반의 필터링/정렬로 추천 목록을 제공합니다.
- 주요 모듈: `recommend_movie.py` (영화 추천 로직 설계 및 데이터 가공 후 반환)
- 구현 포인트:
  - 장르/언어/국가/연도 등 파라미터 
  - `overview` 결측치 기본 문구 대체 및 **표시 길이 제한(예: 200자)** 처리
  - 포스터/백드롭 기본 이미지 대체
  #### <<<추가내용 기술>>>

  ![2](/static/readme_img/2_recommend_example.png)
  > 평점 슬라이딩 방식으로 바꾸고 수정예정

  ![2](/static/readme_img/2_2_recommend_example.png)

### 3) 배우검색 (Actor Search)
- 배우명으로 검색하여 기본 프로필 및 대표작(필모그래피)을 보여줍니다.
- 주요 모듈: `search_actor.py`, `tmdb_helpers.py`

  ![3](/static/readme_img/3_find_actor_example.png)

### 4) 미니게임 (Mini Game)
- TMDb 데이터로 간단한 퀴즈/맞히기 게임을 구성합니다.
- 주요 모듈: `movie_game_app.py`, `game_helpers.py`
- 예: 포스터만 보고 개봉 순서로 맞추기 (1 to 9 Game)

  ![4](/static/readme_img/4_game_example.png)
---

## Project Structure

```
Python_My_Cinema/
├─ app.py                   # Main Flask app (routes)
├─ aws.py                   # AWS Rekognition wrapper
├─ tmdb_helpers.py          # TMDb utilities (requests, image URL, genre mapping)
├─ recommend_movie.py       # Recommendation logic (Discover API, DataFrame processing)
├─ search_actor.py          # Actor search / profile / filmography
├─ movie_game_app.py        # Game logic (rounds, scoring)
├─ game_helpers.py          # Game helpers (question generation, validation)
├─ templates/               # HTML templates
├─ static/                  # CSS, JS, images
├─ .env                     # Environment variables
└─ README.md
```

---

## 빠른 시작

### 1) Requirements
- Python 3.9+
- TMDb API Key
- AWS Access Key/Secret, Region

### 2) 설치

```bash
# Use in virtual environment (recommended)
pip install -r requirements.txt
```

### 3) 환경 변수 설정
Create a .env file in the root (see .env.example):

```dotenv
TMDB_API_KEY=your_tmdb_api_key
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=ap-northeast-2

```

### 4) Run Application

```bash
python app.py
```
---

## File Responsibilities & Dependencies

### `app.py`
- Flask 앱 생성, 라우팅, 템플릿 렌더링, 파일 업로드 처리
- 기능 라우트에서 각 모듈 호출(`aws.py`, `recommend_movie.py`, `search_actor.py`, `movie_game_app.py`)
- **Dependencies**: Flask, requests, pandas, boto3 등

### `aws.py`
- Rekognition API 호출(예: `DetectFaces`, `RecognizeCelebrities`)
- 이미지 바이트 변환/전처리 후 결과를 웹 표시용 구조로 반환
- **Dependencies**: boto3

### `tmdb_helpers.py`

### `recommend_movie.py`
- Discover/Recommendations 파라미터 구성: `with_genres`, `with_origin_country`,
  `with_runtime.gte/lte`, `language`, `sort_by`, `page` 등

- TMDb 결과를 DataFrame으로 정리 후 프론트 표시용 컬럼 가공
  - `overview` Truncates/cleans overview text
  - `poster_path`/`backdrop_path`  -> 미존재 시 기본 이미지로 대체

- **Dependencies**: pandas, requests

### `search_actor.py`
  <!-- Type Here -->

### `movie_game_app.py`
  <!-- Type Here -->

### `game_helpers.py`
  <!-- Type Here -->



---

## Example Endpoints

- `GET /` — 홈
- `GET /face` / `POST /face` — 이미지 업로드 → 얼굴찾기 결과
- `GET /recommend` — 필터 폼 + 추천 결과(페이지/정렬)
- `GET /actor` — 배우 검색 폼 + 결과/상세
- `GET /game` — 게임 시작/다음 라운드/정답 제출

---

## TODO
- `requirements.txt` update
- 