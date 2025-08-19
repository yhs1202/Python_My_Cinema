# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template

# tmdb_helpers에서 얼굴 인식에 필요한 함수를 가져옵니다.
from tmdb_helpers import process_celeb_face 
# search_actor에서 검색 로직과 상세 페이지 로직을 가져옵니다.
from search_actor import process_actor_search, get_actor_details

if not os.path.exists("static"):
    os.mkdir("static")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))

# --- Page Rendering Routes ---

@app.route("/")
def index():
    return render_template("pj_prac.html")

@app.route("/find_actor")
def find_actor():
    return render_template("find_actor.html")
    
@app.route("/search_actor")
def search_actor_page():
    return render_template("search_actor.html")

@app.route("/actor/<int:actor_id>")
def actor_detail(actor_id):
    return get_actor_details(actor_id)

# --- API Routes ---

@app.route("/find_celeb_face", methods=["POST"])
def find_celeb_face():
    return process_celeb_face()

@app.route("/api/search-actors")
def api_search_actors():
    return process_actor_search()

# --- Server Start ---

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)