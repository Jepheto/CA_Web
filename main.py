from flask import Flask, request, render_template
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest
from google.oauth2 import service_account
import aiohttp
import asyncio
import os
import time_conversion_system

# .env에서 가져오기
load_dotenv()
API_KEY = os.getenv("API_KEY")
PROPERTY_ID = os.getenv("PROPERTY_ID")
CREDENTIALS_PATH = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)
client = BetaAnalyticsDataClient(credentials=credentials)

# Flask
app = Flask(__name__)

def get_now_utc_time():
    """현재 UTC 시간 반환"""
    return datetime.now(timezone.utc)

def get_today_and_total_views():
    """GA4 누적 조회 수 + 오늘 방문 수 가져오기"""
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[],
        metrics=[
            {"name": "screenPageViews"}, 
            {"name": "activeUsers"}
        ],
        date_ranges=[
            {"start_date": "2020-01-01", "end_date": "today"},
            {"start_date": "today", "end_date": "today"},
        ]
    )
    response = client.run_report(request)

    total_views = int(response.rows[0].metric_values[0].value) if len(response.rows) > 0 else 0
    today_users = int(response.rows[1].metric_values[1].value) if len(response.rows) > 1 else 0

    return total_views, today_users

def get_last_7_days_visits_and_views():
    """GA4 최근 7일 (오늘까지) 방문자 수 + 조회 수 가져오기 (UTC 기준)"""
    today = get_now_utc_time()
    start_date = (today - timedelta(days=6)).strftime("%Y-%m-%d")  # 6일 전부터
    end_date = today.strftime("%Y-%m-%d")  # 오늘까지

    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[{"name": "date"}],
        metrics=[
            {"name": "activeUsers"},
            {"name": "screenPageViews"}
        ],
        date_ranges=[{"start_date": start_date, "end_date": end_date}],
        order_bys=[{
            "dimension": {"dimension_name": "date"},
            "desc": False
        }]
    )

    response = client.run_report(request)

    # 오늘 포함 7일치 날짜 리스트 만들기
    date_list = []
    for i in range(6, -1, -1):  # 6~0
        date = today - timedelta(days=i)
        formatted_date = f"{date.month:02}/{date.day:02}"
        date_list.append(formatted_date)

    visits_dict = {date: 0 for date in date_list}
    views_dict = {date: 0 for date in date_list}

    if response.rows:
        for row in response.rows:
            if len(row.metric_values) >= 2:
                raw_date = row.dimension_values[0].value
                formatted_date = f"{raw_date[4:6]}/{raw_date[6:]}"
                if formatted_date in visits_dict:
                    visits_dict[formatted_date] = int(row.metric_values[0].value)
                    views_dict[formatted_date] = int(row.metric_values[1].value)
            else:
                print(f"⚠️ 경고: metric_values 부족 - {row}")
    else:
        print("⚠️ 경고: GA4 데이터가 없습니다 (response.rows 비어있음)")

    visits = [visits_dict[date] for date in date_list]
    views = [views_dict[date] for date in date_list]

    return date_list, visits, views

@app.route("/")
def home():
    try:
        total_views, today_users = get_today_and_total_views()
        dates, visits, views = get_last_7_days_visits_and_views()
    except Exception as e:
        print(f"GA4 데이터 가져오기 오류: {e}")
        total_views, today_users = 0, 0
        dates, visits, views = [], [], []
    
    return render_template(
        "home.html",
        total_views=total_views,
        today_users=today_users,
        dates=dates,
        visits=visits,
        views=views
    )

@app.route('/add-bot')
def add_bot():
    return render_template('add-bot.html')

@app.route('/user', methods=['GET'])
def get_user():
    user_id = request.args.get('id')
    if not user_id:
        return render_template('error.html',
                               error_message="ID를 입력해주세요.")

    success, result = asyncio.run(fetch_user_data(user_id))
    return result

async def fetch_user_data(user_id):
    headers = {"x-nxopen-api-key": API_KEY}
    async with aiohttp.ClientSession() as session:
        try:
            # 사용자 ID 정보 조회
            id_url = f'https://open.api.nexon.com/ca/v1/id?user_name={user_id}&world_name=해피'
            async with session.get(id_url, headers=headers) as id_response:
                if id_response.status == 400:
                    return False, render_template('error.html',
                                                  error_message="존재하지 않는 아이디이거나, 2022년 1월 1일 이후로 로그인이 없는 아이디일 수 있습니다.")
                id_data = await id_response.json()

            ouid = id_data.get("ouid")
            # 유저 기본 정보 조회
            user_url = f'https://open.api.nexon.com/ca/v1/user/basic?ouid={ouid}'
            async with session.get(user_url, headers=headers) as user_response:
                if user_response.status == 404:
                    return False, render_template('error.html',
                                                  error_message="유저 정보를 찾을 수 없습니다.")
                user_data = await user_response.json()

            # 길드 정보 조회
            guild_url = f'https://open.api.nexon.com/ca/v1/user/guild?ouid={ouid}'
            async with session.get(guild_url, headers=headers) as guild_response:
                guild_data = await guild_response.json() if guild_response.status == 200 else None

            # 온라인 여부 및 시간 정보 처리
            online_info = time_conversion_system.is_online(user_data["user_date_last_login"],
                                                            user_data["user_date_last_logout"])
            user_info = {
                "user_id": user_id or "정보 없음",
                "level": str(user_data.get("user_level", "0")),
                "exp": str(user_data.get("user_exp", 0)),
                "id_birthday": time_conversion_system.format_ID_birthday_message(user_data.get("user_date_create")) if user_data.get("user_date_create") else "정보 없음",
                "last_login": time_conversion_system.format_last_login_message(user_data.get("user_date_last_login")) if user_data.get("user_date_last_login") else "정보 없음",
                "last_logout": time_conversion_system.format_last_logout_message(user_data.get("user_date_last_logout")) if user_data.get("user_date_last_logout") else "정보 없음",
                "is_online": online_info.get("status", False),
                "check_message": online_info.get("message", "정보 없음"),
                "guild_info": str(guild_data.get("guild_id")) if guild_data and "guild_id" in guild_data else "길드 없음"
                }

            return True, render_template('result.html', user_info=user_info)

        except aiohttp.ClientError:
            return False, render_template('error.html',
                                          error_message="서버가 불안정합니다. 잠시 후 다시 시도해 주세요.")
        except Exception as e:
            return False, render_template('error.html',
                                          error_message=f"알 수 없는 오류가 발생했습니다: {str(e)}")

if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=5000, debug=True)
    app.run (debug=True)