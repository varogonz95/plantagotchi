import urequests

def get_current_time(timezone: str):
    response = urequests.get(f"http://worldtimeapi.org/api/timezone/{timezone}")
    return response.json()