import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # 검색 횟수를 저장할 테이블 생성 (없으면 생성)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usage_stats (
            id INTEGER PRIMARY KEY,
            search_count BIGINT NOT NULL
        );
    """)
    # 단일 행(row)이 존재하는지 확인 (id=1)
    cur.execute("SELECT search_count FROM usage_stats WHERE id = 1;")
    row = cur.fetchone()
    if row is None:
        cur.execute("INSERT INTO usage_stats (id, search_count) VALUES (1, 0);")
    conn.commit()
    cur.close()
    conn.close()

def load_search_count():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT search_count FROM usage_stats WHERE id = 1;")
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return row[0]
    return 0

def save_search_count(count):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE usage_stats SET search_count = %s WHERE id = 1;", (count,))
    conn.commit()
    cur.close()
    conn.close()

# DB 초기화: 모듈이 로드될 때 테이블 생성 및 초기 행이 설정되도록 함
init_db()
