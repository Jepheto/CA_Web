from flask import Flask, request, render_template
from dotenv import load_dotenv
import aiohttp
import asyncio
import os

# .env 파일 로드
load_dotenv()

# 환경 변수에서 API Key 가져오기
API_KEY = os.getenv("API_KEY")

# 폴더에 있는 파일 가져오기
import time_conversion_system

# Flask
app = Flask(__name__)

async def fetch(session, url, headers):
    async with session.get(url, headers=headers) as response:
        if response.status == 400:
            return None, 400
        response.raise_for_status()
        return await response.json(), response.status

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/user', methods=['GET'])
def get_user():
    user_id = request.args.get('id')
    if not user_id:
        return render_template('error.html', error_message="ID를 입력해주세요.")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(fetch_user_data(user_id))
    return result

async def fetch_user_data(user_id):
    headers = {"x-nxopen-api-key": API_KEY}
    async with aiohttp.ClientSession() as session:
        try:
            id_url = f'https://open.api.nexon.com/ca/v1/id?user_name={user_id}&world_name=해피'
            async with session.get(id_url, headers=headers) as id_response:
                if id_response.status == 404:
                    return render_template('error.html', error_message="존재하지 않는 아이디이거나, 2022년 1월 1일 이후로 로그인이 없는 아이디일 수 있습니다.")
                id_data = await id_response.json()

            ouid = id_data.get("ouid")
            user_url = f'https://open.api.nexon.com/ca/v1/user/basic?ouid={ouid}'
            async with session.get(user_url, headers=headers) as user_response:
                if user_response.status == 404:
                    return render_template('error.html', error_message="유저 정보를 찾을 수 없습니다.")
                user_data = await user_response.json()

            # user_info에 적용하기 위해서 미리 뽑은 dict형태의 정보.
            online_info = time_conversion_system.is_online(user_data["user_date_last_login"], user_data["user_date_last_logout"])
            user_info = {
                "user_id": user_id,
                "level": user_data.get("user_level", "알 수 없음"),
                "id_birthday": time_conversion_system.format_ID_birthday_message(user_data.get("user_date_create")),
                "last_login": time_conversion_system.format_last_login_message(user_data.get("user_date_last_login")),
                "last_logout": time_conversion_system.format_last_logout_message(user_data.get("user_date_last_logout")),
                "is_online": online_info["status"],
                "check_message": online_info["message"]
            }

            return render_template('result.html', user_info=user_info)

        except aiohttp.ClientError:
            return render_template('error.html', error_message="서버가 불안정합니다. 잠시 후 다시 시도해 주세요.")
        except Exception as e:
            return render_template('error.html', error_message=f"알 수 없는 오류가 발생했습니다: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)
