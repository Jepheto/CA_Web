from datetime import datetime, timedelta

def _format_timestamp(timestamp):
    """
    ISO 포맷의 타임스탬프에 9시간을 더한 후,
    "YYYY년 M월 D일 H시 M분" 형식의 문자열로 반환.
    """
    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    dt += timedelta(hours=9)
    return f'{dt.year}년 {dt.month}월 {dt.day}일 {dt.hour}시 {dt.minute}분'

def format_last_login_message(timestamp):
    return _format_timestamp(timestamp)

def format_last_logout_message(timestamp):
    return _format_timestamp(timestamp)

def format_ID_birthday_message(timestamp):
    return _format_timestamp(timestamp)

def is_online(last_login, last_logout):
    """
    로그인과 로그아웃 시간의 차이를 바탕으로 온라인 상태를 판단.
    
    - 두 시간이 1초 이하로 차이난다면, 접속 중일 가능성이 높음.
    - 차이가 10초 이하인 경우, 판단이 부정확할 수 있으므로 login_time > logout_time 여부를 그대로 사용.
    - 그 외의 경우는 login_time이 logout_time보다 늦으면 온라인, 그렇지 않으면 오프라인으로 간주.
    """
    if not last_login or not last_logout:
        return {"status": False, "message": "로그인 또는 로그아웃 정보가 없습니다."}
    
    login_time = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
    logout_time = datetime.fromisoformat(last_logout.replace('Z', '+00:00'))
    diff = abs((login_time - logout_time).total_seconds())

    if diff <= 1:
        return {"status": True, "message": "로그인과 로그아웃 시간이 1초 이내로 차이가 납니다. 접속 중일 가능성이 높습니다."}
    elif diff <= 10:
        online = login_time > logout_time
        return {"status": online, "message": "로그인과 로그아웃 시간이 10초 이내로 차이가 납니다. 상태 판단이 정확하지 않을 수 있습니다."}
    else:
        return {"status": login_time > logout_time, "message": "정상적으로 접속 상태를 판단했습니다."}
