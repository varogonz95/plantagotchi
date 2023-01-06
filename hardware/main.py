import utime
from array import array

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
RTC_SET = False
# ###################################################################################

# INITIALIZE PERIPHERALS ############################################################
builtin_led = Pin(2, Pin.OUT)
rtc = RTC()
wlan = wlan_client.init(network.STA_IF)
i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
oled = OLEDDisplay_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)
soil_moist = ADC(Pin(34), atten=ADC.ATTN_11DB)
ldr = ADC(Pin(35), atten=ADC.ATTN_11DB)
# dht11_sensor = DHT11(Pin(19))
# ###################################################################################

def draw_sad_face():
    oled.fill_rect(50, 24, 4, 4, 1)
    oled.fill_rect(74, 24, 4, 4, 1)
    oled.hline(52, 36, 24, 4)
    oled.pixel(51, 37, 1)
    oled.pixel(76, 37, 1)
    oled.pixel(50, 38, 1)
    oled.pixel(77, 38, 1)
    oled.show()

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

def signal_intensity(rssi):
    return ((5/6)*int(rssi)) + 100

def handle_exception(ex: Exception):
    print(str(ex))
    oled.fill(0)
    oled.text_line('An error occured', 1)
    draw_sad_face()

# def display_dht11_readings(dht11_sensor: DHT11, h_line, t_line):
#     humidity = dht11_sensor.humidity()
#     temp = dht11_sensor.temperature()
#     oled.text_line(f'Humidity: {humidity}%', h_line)
#     oled.text_line(f'Temp: {temp}C', t_line)

def parse_rssi(x) -> float:
    return (5*x/3) + 150

def parse_soil_moisture(x) -> float:
    return 100 - (20*x/819)

def create_document(data: dict):
    fields={}
    for key, value in data.items():
        valueType='Value'
        if type(value) is None:
            valueType = 'null' + valueType
        if type(value) is bool:
            valueType = 'boolean' + valueType
        if type(value) is int:
            valueType = 'integer' + valueType
        if type(value) is float:
            valueType = 'double' + valueType
        if type(value) is str:
            valueType = 'string' + valueType
        if type(value) is list or type(value) is tuple:
            valueType = 'array' + valueType
        fields[key]= {valueType: value}
    return {'fields': fields}

def display_sensors(sensors: dict):
    oled.text_line(f'Wifi:  {"%.2f" % sensors["rssi"]}', 3)
    oled.text_line(f'Soil:  {"%d" % sensors["soil_parsed_value"]}%', 4)
    oled.text_line(f'Light: {sensors["ldr_raw_value"]}', 5)

def post_sensors_data(data):
    urequests.post(
        f'https://firestore.googleapis.com/v1/projects/{FIRESTORE_PROJECT_ID}/databases/(default)/documents/sensors',
        json=create_document(data),
        headers={
            'Content-Type': 'application/json',
            'key': FIRESTORE_API_KEY
        },
    ).close()

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

wlan.config(reconnects=5)

# Show project name
oled.fill(0)
oled.text_line(PROJECT_NAME, 1)
oled.hline(0, 12 ,128, 2)
request_interval_count = SEND_REQUEST_INTERVAL

try:
    response = remote_time.get_current_time(TIMEZONE)
    rtc.datetime()
    RTC_SET = True
    print(f"unixtime: {response['unixtime']}")
except Exception as e:
    print("Unable to get remote time")
    print(f"Error: {e}")

while True:
    try:
        rssi_raw_value = wlan.status('rssi') if wlan.isconnected() else -100
        rssi = (rssi_raw_value)
        soil_raw_value = soil_moist.read()
        ldr_raw_value = ldr.read()

        sensors_data: dict = {
            'rssi': rssi,
            'soil_raw_value': soil_raw_value,
            'soil_parsed_value': parse_soil_moisture(soil_raw_value),
            'ldr_raw_value': ldr_raw_value,
        }

        draw_signal(120, 6, rssi)
        display_sensors(sensors_data)

        oled.clear_line(8)
        if not try_connect(MAX_RECONNECTS, builtin_led):
            builtin_led.off()
            oled.text_line("Not connected...", 8)
            print("Failed to reconnect...")
        elif request_interval_count >= SEND_REQUEST_INTERVAL and RTC_SET:
                print("Sending data...")
                oled.text_line("Sending data...", 8)
                post_sensors_data(sensors_data)
                request_interval_count = 0

        request_interval_count += 1
        utime.sleep(1)
    except Exception as exc:
        if 'Wifi' in str(exc):
            for i in range(3, 8):
                oled.clear_line(i)
            oled.text_line(str(exc), 3)
        else:
            oled.text_line("Error", 1)
            exc_as_str = str(exc)
            print(exc_as_str)
            for i, w in enumerate(exc_as_str.split(' ')):
                oled.text_line(w, i+3)
