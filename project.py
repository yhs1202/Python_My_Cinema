# request : client -> server
# response : server -> client

#Python Server
##1) flask : 마이크로 웹 프레임워크 (12000 line)
##2) Django : 모든 기능이 포함 (flask보다 10~12배 무거움)

#가상환경 변경하는 법 : 우측 하단 3.9.13 혹은 가상환경 이름을 클릭 또는 Ctrl + Shift + P-> 인터프리터 검색 -> 인터프리터 선택
from flask import Flask             #route 경로, run 서버 실행
from flask import render_template   #html load
from flask import request           #사용자가 보낸 정보
from flask import redirect          #페이지 이동
from flask import make_response     # 페이지 이동 시 정보 유지
from flask import jsonify

#aws.py 안의 detect_labels_local_file 함수만 쓰고 싶다
from aws import recognize_celebrities

#파일 이름 보안처리 라이브러리
from werkzeug.utils import secure_filename

import os
#static 폴더가 없으면 만들기
if not os.path.exists("static"):
    os.mkdir("static")

app = Flask(__name__)

# 루트 페이지 (처음 접속하는 페이지)
# 루트 페이지
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
    app.run(host="0.0.0.0", port=5000)
