import sys
import os
import random
import time
import requests
from dotenv import load_dotenv
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QGridLayout
from PyQt5.QtGui import QFont, QPixmap, QIcon

# 프로그램 시작 시 .env 파일에서 환경 변수를 로드
load_dotenv()

def get_popular_movies():
    """TMDB API를 사용해 인기 영화 목록 9개를 안전하게 가져오는 함수"""
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        print("오류: TMDB_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
        return None

    random_page = random.randint(1, 10)
    url = (f"https://api.themoviedb.org/3/discover/movie?"
           f"api_key={api_key}"
           f"&language=ko-KR"
           f"&sort_by=popularity.desc"
           f"&page={random_page}"
           f"&with_watch_monetization_types=flatrate")

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()['results']
        
        movies = []
        for movie in data:
            if movie.get('poster_path') and movie.get('release_date'):
                movies.append({
                    'id': movie['id'],
                    'title': movie['title'],
                    'poster_path': movie['poster_path'],
                    'release_date': movie['release_date']
                })
            if len(movies) == 9:
                break
        
        return movies if len(movies) == 9 else None

    except requests.exceptions.RequestException as e:
        print(f"API 요청 중 오류가 발생했습니다: {e}")
        return None

class MovieGameApp(QWidget):
    """PyQt5를 사용한 영화 퀴즈 게임 메인 클래스"""
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        """UI의 초기 레이아웃과 위젯을 설정합니다."""
        self.setWindowTitle("Find the Oldest Movie Game")
        self.setGeometry(300, 300, 450, 700)

        vbox = QVBoxLayout()
        self.ql_info = QLabel("Find the Oldest Movie", alignment=Qt.AlignCenter)
        self.ql_info.setFont(QFont("Arial", 24, QFont.Bold))
        self.btn_start = QPushButton("GAME START")
        self.btn_start.setFixedHeight(40)
        grid = QGridLayout()
        grid.setSpacing(12)

        self.b_list = []
        for row in range(3):
            for col in range(3):
                btn = QPushButton()
                btn.setMinimumSize(120, 180)
                grid.addWidget(btn, row, col)
                self.b_list.append(btn)
                btn.clicked.connect(self.btn_clicked)

        vbox.addStretch(1)
        vbox.addWidget(self.ql_info)
        vbox.addWidget(self.btn_start, alignment=Qt.AlignCenter)
        vbox.addLayout(grid)
        vbox.addStretch(1)
        self.setLayout(vbox)
        
        self.disable_all_buttons()
        self.btn_start.clicked.connect(self.game_start)
        self.show()

    def disable_all_buttons(self):
        """모든 게임 버튼을 비활성화하고 아이콘을 초기화합니다."""
        for btn in self.b_list:
            btn.setEnabled(False)
            btn.setIcon(QIcon())
            if hasattr(btn, 'movie_data'):
                delattr(btn, 'movie_data')

    def game_start(self):
        """GAME START 버튼을 누르면 호출되는 함수"""
        self.ql_info.setText("Loading Movies...")
        QApplication.processEvents()

        movies = get_popular_movies()
        if not movies:
            self.ql_info.setText("Failed to load movies!")
            return

        self.correct_sequence = sorted(movies, key=lambda x: x['release_date'])
        random.shuffle(movies)
        self.current_step = 0
        self.start_time = time.time()
        self.ql_info.setText(f"Click the Oldest Movie! ({self.current_step + 1}/9)")

        for btn, movie in zip(self.b_list, movies):
            poster_url = f"https://image.tmdb.org/t/p/w200{movie['poster_path']}"
            pixmap = QPixmap()
            try:
                response = requests.get(poster_url, stream=True)
                response.raise_for_status()
                image_data = response.content
                pixmap.loadFromData(image_data)
                btn.setIcon(QIcon(pixmap))
                btn.setIconSize(QSize(120, 180))
                btn.setEnabled(True)
                btn.movie_data = movie
            except requests.exceptions.RequestException as e:
                print(f"이미지 다운로드에 실패했습니다: {e}")
                btn.setText("Image\nError")
                btn.setEnabled(False)

    def btn_clicked(self):
        """영화 포스터 버튼이 클릭되었을 때 호출되는 함수"""
        clicked_btn = self.sender()
        clicked_movie = clicked_btn.movie_data

        if clicked_movie['id'] == self.correct_sequence[self.current_step]['id']:
            clicked_btn.setEnabled(False)
            self.current_step += 1
            if self.current_step == 9:
                end_time = time.time()
                record = end_time - self.start_time
                self.ql_info.setText(f"Success! Record: {record:.2f} Sec")
                self.disable_all_buttons()
            else:
                self.ql_info.setText(f"Correct! ({self.current_step + 1}/9)")
        else:
            self.ql_info.setText("Wrong! Try again.")

if __name__ == "__main__":
    app = QApplication.instance() or QApplication(sys.argv)
    game = MovieGameApp()
    sys.exit(app.exec_())