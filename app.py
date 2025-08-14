# -*- coding: utf-8 -*-
from flask import Flask             # route 경로, run 서버 실행
from flask import render_template   # html load
from flask import request           # 사용자가 보낸 정보
from flask import redirect          # 페이지 이동
from flask import make_response     # 페이지 이동 시 정보 유지
from flask import jsonify

from aws import recognize_celebrities
from werkzeug.utils import secure_filename
import os

# Ensure the static directory exists
if not os.path.exists("static"):
    os.mkdir("static")

app = Flask(__name__)

# root page
@app.route("/")
def index():
    return render_template("pj_prac.html")

# find_actor 페이지
@app.route("/find_actor")
def find_actor():
    return render_template("find_actor.html")

# 얼굴 인식 POST 요청 처리
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

    # AWS 얼굴 인식 함수 호출
    celeb_info = recognize_celebrities(save_path)
    
    # 결과를 JSON 형태로 반환합니다.
    return jsonify(celeb_info)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
