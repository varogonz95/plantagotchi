import _thread
import time

import network
import urequests
from machine import ADC, RTC, Pin, SoftI2C

import constants as Const
from lib import app_sensors as sensors
from lib import oled_display as oled
from lib import remote_time, wlan_client

# from dht11 import DHT11

# INIT ------------------------------------------------------------------------------
builtin_led = Pin(2, Pin.OUT)
rtc = RTC()
boot_btn = Pin(0, Pin.IN, Pin.PULL_DOWN)
i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
display = oled.Display_I2C(Const.OLED_WIDTH, Const.OLED_HEIGHT, i2c)
wlan = wlan_client.init(network.STA_IF)
soil_adc = ADC(Pin(34), atten=ADC.ATTN_11DB)
ldr_adc = ADC(Pin(35), atten=ADC.ATTN_11DB)

wlan.config(reconnects=5)
display.fill(0)
display.hline(0, 12 ,128, 2)
# /INIT -----------------------------------------------------------------------------

# FUNCTIONS -------------------------------------------------------------------------
def is_pressed(btn):
    return not btn.value()

def show_calibration_menu():
    display.text_line('Calibration', 1)

def display_sensors(sensors: dict):
    for i, value in enumerate(sensors.values()):
        print(f"{value.get('name')}: {value.get('raw_value')}")
        display.text_line(f"{value.get('name')}: {value.get('display_value')}", i+3)

def handle_exception(exc: Exception):
    exc_as_str = str(exc)
    print(exc_as_str)
    for i, w in enumerate(exc_as_str.split(' ')):
        display.text_line(w, i + 3)
# /FUNCTIONS ------------------------------------------------------------------------

ldr = sensors.LdrSensor(ldr_adc)
soil = sensors.SoilSensor(soil_adc)

selected_sensor = ldr.name
initial_time = time.time()
current_workflow = Const.MONITOR_WORKFLOW

def keep_posting_data(latest_request):
    def try_connect(retries = 1, led = None):
        retry_count = 0
        # While network is available
        #   and has remaining retries
        while retry_count < retries and not wlan.isconnected() and wlan_client.is_nearby(wlan, Const.SSID):
            display.text_line("Connecting...", 8)
            wlan_client.connect(wlan, Const.SSID, Const.PSSW, indicator_gpio = led)
            retry_count += 1
        display.clear_lines([8])
        # Check if connection succeded after retries
        return wlan.isconnected()

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

    def post_sensors_data(data):
        return urequests.post(
            f'https://firestore.googleapis.com/v1/projects/{Const.FIRESTORE_PROJECT_ID}/databases/(default)/documents/sensors',
            json=data,
            headers={
                'Content-Type': 'application/json',
                'key': Const.FIRESTORE_API_KEY
            },
        )
   
    while True:
        now = time.time()
        elapsed_time = now - latest_request
        try:
            if not try_connect(Const.MAX_RECONNECTS, builtin_led):
                builtin_led.off()
                display.text_line("Not connected...", 8)
                print("Failed to reconnect...")
            elif elapsed_time >= Const.SEND_REQUEST_SECS:
                print("Sending data...")
                display.text_line("Sending data...", 8)
                documentData = create_document({
                    'ldr': ldr.as_dict(),
                    'soil': soil.as_dict()
                })
                current_time = remote_time.get_current_time(Const.TIMEZONE).get('datetime')
                documentData['fields']['created_at'] = {'timestampValue': current_time}
                print(documentData)
                post_sensors_data(documentData).close()
                display.clear_lines([8])
                latest_request = now
            time.sleep(1)
        except Exception as exc:
            handle_exception(exc)
            time.sleep(5)
            display.clear_lines(range(1, 9))

_thread.start_new_thread(keep_posting_data, (initial_time,))

while True:
    if is_pressed(boot_btn):
        current_workflow = Const.CALIBRATION_WORKFLOW

    if current_workflow is Const.MONITOR_WORKFLOW:
        display.text_line("Plantagotchi", 1)
        display_sensors({
            'ldr': ldr.as_dict(),
            'soil': soil.as_dict()
        })
        time.sleep(1)
    if current_workflow is Const.CALIBRATION_WORKFLOW:
        show_calibration_menu()
