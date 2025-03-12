from flask import Flask, request, render_template
import os

app = Flask(__name__)

# 🔹 검색 횟수를 저장할 파일 경로
SEARCH_COUNT_FILE = "search_count.txt"

# 🔹 서버가 시작될 때 검색 횟수를 불러오기
def load_search_count():
    if os.path.exists(SEARCH_COUNT_FILE):
        with open(SEARCH_COUNT_FILE, "r") as file:
            try:
                return int(file.read().strip())
            except ValueError:
                return 0  # 파일이 손상되었을 경우 초기화
    return 0

# 🔹 검색 횟수를 파일에 저장
def save_search_count(count):
    with open(SEARCH_COUNT_FILE, "w") as file:
        file.write(str(count))

# 🔹 검색 횟수 초기 로드
search_count = load_search_count()

@app.route('/')
def home():
    return render_template("home.html", search_count=search_count)

@app.route('/user', methods=['GET'])
def get_user():
    global search_count

    # 🔹 검색 횟수 증가 & 저장
    search_count += 1
    save_search_count(search_count)

    return render_template("result.html", search_count=search_count)

if __name__ == "__main__":
    app.run(debug=True)