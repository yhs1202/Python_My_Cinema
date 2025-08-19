# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

from aws import recognize_celebrities
# 새로 만든 tmdb_person_external_ids 함수를 import 목록에 추가합니다.
from tmdb_helpers import tmdb_search_person_id, tmdb_person_details, tmdb_person_external_ids

if not os.path.exists("static"):
    os.mkdir("static")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))

@app.route("/")
def index():
    return render_template("pj_prac.html")

@app.route("/find_actor")
def find_actor():
    return render_template("find_actor.html")

@app.route("/find_celeb_face", methods=["POST"])
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

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
