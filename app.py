# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template, request, jsonify

# 새로 만든 tmdb_person_external_ids 함수를 import 목록에 추가합니다.
from tmdb_helpers import *

if not os.path.exists("static"):
    os.mkdir("static")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))

# ---------------- FIND ACTOR SERVICE ----------------
@app.route("/")
def index():
    return render_template("pj_prac.html")

@app.route("/find_actor")
def find_actor():
    return render_template("find_actor.html")

@app.route("/find_celeb_face", methods=["POST"])
def find_celeb_face():
    return process_celeb_face()


# ---------------- MOVIE RECOMMENDATION SERVICE ----------------
@app.route("/recommend_mv", methods=["GET", "POST"])
def recommend_movie():
    return render_template("recommend_mv.html")


@app.route("/get_recommendations", methods=["POST"])
def get_recommendations():
    pass




if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
