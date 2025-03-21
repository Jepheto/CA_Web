from flask import Flask, request, render_template
from dotenv import load_dotenv
import aiohttp
import asyncio
import os
import time_conversion_system
import search_counting_machine  # 파일 기반 대신 DB 모듈 사용

load_dotenv()

API_KEY = os.getenv("API_KEY")
app = Flask(__name__)

# DB에서 검색 횟수를 불러옴
search_count = search_counting_machine.load_search_count()

@app.route('/')
def home():
    return render_template('home.html', search_count=search_count)

@app.route('/add-bot')
def add_bot():
    return render_template('add-bot.html')

@app.route('/user', methods=['GET'])
def get_user():
    global search_count
    user_id = request.args.get('id')
    if not user_id:
        return render_template('error.html',
                               error_message="ID를 입력해주세요.",
                               search_count=search_count)

    # 비동기 함수 실행
    success, result = asyncio.run(fetch_user_data(user_id))

    # 유효한 ID라면 검색 횟수를 증가시키고 DB에 저장
    if success:
        search_count += 1
        search_counting_machine.save_search_count(search_count)

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
                                                  error_message="존재하지 않는 아이디이거나, 2022년 1월 1일 이후로 로그인이 없는 아이디일 수 있습니다.",
                                                  search_count=search_count)
                id_data = await id_response.json()

            ouid = id_data.get("ouid")
            # 유저 기본 정보 조회
            user_url = f'https://open.api.nexon.com/ca/v1/user/basic?ouid={ouid}'
            async with session.get(user_url, headers=headers) as user_response:
                if user_response.status == 404:
                    return False, render_template('error.html',
                                                  error_message="유저 정보를 찾을 수 없습니다.",
                                                  search_count=search_count)
                user_data = await user_response.json()

            # 길드 정보 조회
            guild_url = f'https://open.api.nexon.com/ca/v1/user/guild?ouid={ouid}'
            async with session.get(guild_url, headers=headers) as guild_response:
                if guild_response.status == 200:
                    guild_data = await guild_response.json()
                else:
                    guild_data = None

            # 온라인 여부 및 시간 정보 처리
            online_info = time_conversion_system.is_online(user_data["user_date_last_login"],
                                                            user_data["user_date_last_logout"])
            user_info = {
                "user_id": user_id,
                "level": user_data.get("user_level", "알 수 없음"),
                "exp": user_data.get("user_exp"),
                "id_birthday": time_conversion_system.format_ID_birthday_message(user_data.get("user_date_create")),
                "last_login": time_conversion_system.format_last_login_message(user_data.get("user_date_last_login")),
                "last_logout": time_conversion_system.format_last_logout_message(user_data.get("user_date_last_logout")),
                "is_online": online_info["status"],
                "check_message": online_info["message"],
                "guild_info": guild_data["guild_id"] if guild_data else None
            }

            return True, render_template('result.html', user_info=user_info, search_count=search_count)

        except aiohttp.ClientError:
            return False, render_template('error.html',
                                          error_message="서버가 불안정합니다. 잠시 후 다시 시도해 주세요.",
                                          search_count=search_count)
        except Exception as e:
            return False, render_template('error.html',
                                          error_message=f"알 수 없는 오류가 발생했습니다: {str(e)}",
                                          search_count=search_count)

if __name__ == '__main__':
    app.run(debug=True)