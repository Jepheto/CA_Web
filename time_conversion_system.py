from datetime import datetime, timedelta

# CA_login_data로 메세지 보내기
def format_last_login_message(timestamp):
    original_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

    # original_time은 실제로 loginNout 한 시간에 9시간이나 느렸다.
    time_difference = timedelta(hours=9)
    last_login_time = original_time + time_difference

    # 계산한 last_login_time을 이용해서 각 결과 저장.
    year = last_login_time.year
    month = last_login_time.month
    day = last_login_time.day
    hours = last_login_time.hour
    minutes = last_login_time.minute

    message = f'{year}년 {month}월 {day}일 {hours}시 {minutes}분'

    return message

def format_last_logout_message(timestamp):
    original_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

    # original_time은 실제로 loginNout 한 시간에 9시간이나 느렸다.
    time_difference = timedelta(hours=9)
    last_logout_time = original_time + time_difference

    # 계산한 last_logout_time을 이용해서 각 결과 저장.
    year = last_logout_time.year
    month = last_logout_time.month
    day = last_logout_time.day
    hours = last_logout_time.hour
    minutes = last_logout_time.minute

    message = f'{year}년 {month}월 {day}일 {hours}시 {minutes}분'

    return message

def format_ID_birthday_message(timestamp):
    original_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

    # original_time은 실제로 loginNout 한 시간에 9시간이나 느렸다.
    time_difference = timedelta(hours=9)
    last_logout_time = original_time + time_difference

    # 계산한 last_logout_time을 이용해서 각 결과 저장.
    year = last_logout_time.year
    month = last_logout_time.month
    day = last_logout_time.day
    hours = last_logout_time.hour
    minutes = last_logout_time.minute

    message = f'{year}년 {month}월 {day}일 {hours}시 {minutes}분'

    return message

def is_online(last_login, last_logout):
    if not last_login or not last_logout:
        return {"status": False, "message": "로그인 또는 로그아웃 정보가 없습니다."}

    login_time = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
    logout_time = datetime.fromisoformat(last_logout.replace('Z', '+00:00'))
    time_difference = abs((login_time - logout_time).total_seconds())

    if time_difference <= 1:
        return {"status": True, "message": "로그인과 로그아웃 시간이 1초 이내로 차이가 납니다. 접속 중일 가능성이 높습니다."}
    elif time_difference <= 10:
        return {"status": login_time > logout_time, "message": "로그인과 로그아웃 시간이 10초 이내로 차이가 납니다. 상태 판단이 정확하지 않을 수 있습니다."}
    else:
        return {"status": login_time > logout_time, "message": "정상적으로 접속 상태를 판단했습니다."}