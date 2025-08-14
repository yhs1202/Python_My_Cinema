from flask import Flask, render_template, request, redirect, make_response
from aws import detect_labels_local_file, compare_faces
from werkzeug.utils import secure_filename

import os

# Ensure the static directory exists
if not os.path.exists("static"):
    os.makedirs("static")
    
app = Flask(__name__)
@app.route("/")
def main_page():
    return render_template("pj_prac.html")  ## Change to your HTML file



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)