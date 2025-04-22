from flask import Flask, request, render_template
from dotenv import load_dotenv
import aiohttp
import asyncio
import os
import time_conversion_system

load_dotenv()

API_KEY = os.getenv("API_KEY")
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

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
                "id_birthday": (time_conversion_system.format_ID_birthday_message(user_data.get("user_date_create")) if user_data.get("user_date_create") else "정보 없음"),
                "last_login": (time_conversion_system.format_last_login_message(user_data.get("user_date_last_login")) if user_data.get("user_date_last_login") else "정보 없음"),
                "last_logout": (time_conversion_system.format_last_logout_message(user_data.get("user_date_last_logout")) if user_data.get("user_date_last_logout") else "정보 없음"),
                "is_online": online_info["status"] if "status" in online_info else False,
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
    app.run(host='0.0.0.0', port=5000, debug=True)
