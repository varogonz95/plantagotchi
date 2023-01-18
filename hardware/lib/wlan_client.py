import time
from network import WLAN

def init(type, active=True) -> WLAN: 
    wlan = WLAN(type)
    wlan.active(active)
    return wlan

def connect(wlan: WLAN, ssid: str, passw: str, retry_timeout = 15, indicator_gpio = None):
    if not wlan.isconnected():
        sleep_time=0.25
        retry_count = 0
        
        wlan.connect(ssid, passw)
        
        while not wlan.isconnected() and retry_count < retry_timeout:
            if indicator_gpio is not None:
                indicator_gpio.value(not indicator_gpio.value())
            retry_count += sleep_time
            time.sleep(sleep_time)
    
    if indicator_gpio is not None:
        indicator_gpio.value(wlan.isconnected())

def disconnect(wlan, indicator_pin=None):
    while wlan.isconnected():
        wlan.active(False)
        if not indicator_pin == None:
            indicator_pin.off()

def is_nearby(wlan: WLAN, ssid: str) -> bool:
    nearby_stations = wlan.scan()
    for st in nearby_stations:
        if st[0] == str.encode(ssid):
            return True
    return False
