import _thread
import time
import re

import network
import urequests
from machine import ADC, RTC, Pin, SoftI2C

import constants as Const
from lib import app_sensors as sensors
from lib import oled_display as oled
from lib import wlan_client

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
def log(txt):
    if Const.ENABLE_LOGS:
        print(txt)

def handle_exception(exc: Exception):
    exc_as_str = str(exc)
    log(exc_as_str)
    for i, w in enumerate(exc_as_str.split(' ')):
        display.text_line(w, i + 3)
# /FUNCTIONS ------------------------------------------------------------------------

ldr = sensors.LdrSensor(ldr_adc)
soil = sensors.SoilSensor(soil_adc)
initial_time = time.time()

def data_pusher_thread(latest_request):
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

            if re.match('^\w+\:\w+$', key):
                keyParts = str(key).split(':')
                valueType = keyParts[1] + valueType
                fields[keyParts[0]] = { valueType: value }
                continue
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
                log("Failed to reconnect...")
            elif elapsed_time >= Const.SEND_REQUEST_SECS:
                log("Sending data...")
                display.text_line("Sending data...", 8)
                # current_time = remote_time.get_current_time(Const.TIMEZONE).get('datetime')
                documentData = create_document({
                    'ldr': ldr.as_dict(),
                    'soil': soil.as_dict(),
                    'created_at:timestamp': now
                })
                post_sensors_data(documentData).close()
                log(documentData)
                display.clear_lines([8])
                latest_request = now
            time.sleep(1)
        except Exception as exc:
            # handle_exception(exc)
            # time.sleep(5)
            # display.clear_lines(range(1, 9))
            pass

def sensor_monitor_thread():
    button_released = True
    current_workflow = Const.MONITOR_WORKFLOW

    def is_pressed(btn):
        return not btn.value()

    def show_calibration_menu(sensors: list):
        log("Calibration menu")
        display.text_line('Calibration', 1)
        for s in sensors:
            display.text_line('> Light', 3)
            display.text_line('  Soil', 4)

    def show_min_sensor_calibration(sensor: sensors.Sensor):
        log(f"{sensor.name} - Min")
        log(f'Voltaje: {sensor.read_voltage()}')
        display.text_line(f"{sensor.name} - Min", 1)
        display.text_line(f'Voltaje: {sensor.read_voltage()}', 3)

    def show_max_sensor_calibration(sensor: sensors.Sensor):
        log(f"{sensor.name} - Max")
        log(f'Voltaje: {sensor.read_voltage()}')
        display.text_line(f"{sensor.name} - Max", 1)
        display.text_line(f'Voltaje: {sensor.read_voltage()}', 3)
        
    def display_sensors(sensors: dict):
        out = []
        for i, value in enumerate(sensors.values()):
            out.append(f"{value.get('name')}: {value.get('raw_value')}")
            display.text_line(f"{value.get('name')}: {value.get('display_value')}", i+3)
        log(", ".join(out))

    while True:
        if is_pressed(boot_btn):
            # REDIRECT TO CALIBRATION MENU
            if current_workflow is Const.MONITOR_WORKFLOW and button_released:
                current_workflow = Const.CALIBRATION_MENU_WORKFLOW
            # REDIRECT TO CALIBRATION MENU
            elif current_workflow is Const.CALIBRATION_MENU_WORKFLOW and button_released:
                current_workflow = Const.SET_SENSOR_MIN_CALIBRATION_VALUE

            elif current_workflow is Const.SET_SENSOR_MIN_CALIBRATION_VALUE and button_released:
                soil.min_value = soil.read_voltage()
                current_workflow = Const.SET_SENSOR_MAX_CALIBRATION_VALUE

            elif current_workflow is Const.SET_SENSOR_MAX_CALIBRATION_VALUE and button_released:
                soil.max_value = soil.read_voltage()
                current_workflow = Const.MONITOR_WORKFLOW

            button_released = False

        elif not button_released:
            button_released = True

        if current_workflow is Const.MONITOR_WORKFLOW:
            display.text_line("Plantagotchi", 1)
            display_sensors({
                'ldr': ldr.as_dict(),
                'soil': soil.as_dict()
            })
            time.sleep(1)
        elif current_workflow is Const.CALIBRATION_MENU_WORKFLOW:
            show_calibration_menu()
            time.sleep_ms(250)
        elif current_workflow is Const.SET_SENSOR_MIN_CALIBRATION_VALUE:
            show_min_sensor_calibration(soil)
            time.sleep_ms(250)
        elif current_workflow is Const.SET_SENSOR_MAX_CALIBRATION_VALUE:
            show_max_sensor_calibration(soil)
            time.sleep_ms(250)

# _thread.start_new_thread(data_pusher_thread, (initial_time,))
_thread.start_new_thread(sensor_monitor_thread, ())

data_pusher_thread(initial_time)
# sensor_monitor_thread()

