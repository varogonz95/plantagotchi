import time
from array import array
from app_sensors import LdrSensor, SoilSensor

import network
import urequests
import wlan_client
import remote_time
# from dht11 import DHT11
from machine import ADC, Pin, SoftI2C, RTC
from oled_display import OLEDDisplay_I2C

# GLOBALS ###########################################################################
PROJECT_NAME = 'Plantagotchi'
SSID='Alvaro-AP'
PSSW='hola1234'
OLED_WIDTH = 128
OLED_HEIGHT = 64
FIRESTORE_API_KEY='AIzaSyAUIuBk5mJt8VqfK4jMvJkizbj0luVPbxI'
FIRESTORE_PROJECT_ID='workshop-fa2ff'
SEND_REQUEST_INTERVAL= 60
MAX_RECONNECTS = 5
TIMEZONE = "America/Costa_Rica"
# ###################################################################################

# INITIALIZE PERIPHERALS ############################################################
builtin_led = Pin(2, Pin.OUT)
rtc = RTC()
wlan = wlan_client.init(network.STA_IF)
i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
oled = OLEDDisplay_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)
soil_adc = ADC(Pin(34), atten=ADC.ATTN_11DB)
ldr_adc = ADC(Pin(35), atten=ADC.ATTN_11DB)

wlan.config(reconnects=5)
oled.fill(0)
# ###################################################################################

def draw_signal(x, y, rssi):
    multiplier = 0

    if rssi <= -90:
        multiplier = 1
    elif rssi <= -70:
        multiplier = 2
    else:
        multiplier = 3

    coords = array('h',[0, 0, -2 * multiplier, -2 * multiplier, -2 * multiplier, 0])
    oled.poly(x, y, coords, 1, True)

def handle_exception(exc: Exception):
    exc_as_str = str(exc)
    print(exc_as_str)
    for i, w in enumerate(exc_as_str.split(' ')):
        oled.text_line(w, i + 3)

def create_document(data: dict):
    fields = {}
    for key, value in data.items():
        valueType='Value'
        if type(value) is None:
            valueType = 'null' + valueType
        elif type(value) is bool:
            valueType = 'boolean' + valueType
        elif type(value) is int:
            valueType = 'integer' + valueType
        elif type(value) is float:
            valueType = 'double' + valueType
        elif type(value) is str:
            valueType = 'string' + valueType
        elif type(value) is list or type(value) is tuple:
            valueType = 'array' + valueType
            raise ValueError('array document fields are not yet supported')
        elif type(value) is dict:
            valueType = 'map' + valueType
            fields[key] = { valueType: create_document(value) }
            continue

        fields[key] = { valueType: value }
    
    return {'fields': fields}

def display_sensors(sensors: dict):
    for i, value in enumerate(sensors.values()):
        print(f"{value.get('name')}: {value.get('raw_value')}")
        oled.text_line(f"{value.get('name')}: {value.get('display_value')}", i+3)

def post_sensors_data(data) -> urequests.Response:
    return urequests.post(
        f'https://firestore.googleapis.com/v1/projects/{FIRESTORE_PROJECT_ID}/databases/(default)/documents/sensors',
        json=data,
        headers={
            'Content-Type': 'application/json',
            'key': FIRESTORE_API_KEY
        },
    )

def try_connect(retries = 1, led = None):
    retry_count = 0
    # While network is available
    #   and has remaining retries
    while retry_count < retries and not wlan.isconnected() and wlan_client.is_nearby(wlan, SSID):
        oled.text_line("Connecting...", 8)
        wlan_client.connect(wlan, SSID, PSSW, indicator_gpio = led)
        retry_count += 1

    # Check if connection succeded after retries
    return wlan.isconnected()

def set_rtc(unixtime):
    time_tuple = time.localtime(unixtime)
    print(f"time_tuple: {time_tuple}")
    rtc.datetime(time_tuple)

ldr = LdrSensor(ldr_adc)
soil = SoilSensor(soil_adc)
request_interval_count = SEND_REQUEST_INTERVAL

while True:
    oled.text_line(PROJECT_NAME, 1)
    oled.hline(0, 12 ,128, 2)

    try:
        # rssi_raw_value = wlan.status('rssi') if wlan.isconnected() else -100
        # rssi = (rssi_raw_value)

        sensors_data: dict = {
            'ldr': ldr.as_dict(),
            'soil': soil.as_dict()
        }

        # draw_signal(120, 6, rssi)
        display_sensors(sensors_data)
        # if not try_connect(MAX_RECONNECTS, builtin_led):
        #     builtin_led.off()
        #     oled.text_line("Not connected...", 8)
        #     print("Failed to reconnect...")
        # elif request_interval_count >= SEND_REQUEST_INTERVAL:
        #         print("Sending data...")
        #         oled.text_line("Sending data...", 8)
        #         documentData = create_document(sensors_data)
        #         current_time = remote_time.get_current_time(TIMEZONE).get('datetime')
        #         documentData['fields']['created_at'] = {'timestampValue': current_time}
        #         print(documentData)
        #         post_sensors_data(documentData).close()
        #         oled.clear_lines([8])
        #         request_interval_count = 0
        # request_interval_count += 1

        time.sleep(1)
    except Exception as exc:
        handle_exception(exc)
        time.sleep(5)
        oled.clear_lines(range(1, 9))