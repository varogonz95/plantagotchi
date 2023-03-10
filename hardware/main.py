import gc
import _thread
import re
import time

import network
import urequests
from machine import ADC, RTC, Pin, SoftI2C
from network import WLAN

import constants as C
from helpers import DisplayHelper
from lib import app_sensors as sensors
from lib import oled_display as oled
from lib import remote_time, wlan_client

# INIT ------------------------------------------------------------------------------
builtin_led = None
rtc = None
boot_btn = None
i2c = None
display = None
soil_adc = None
ldr_adc = None

try:
    builtin_led = Pin(2, Pin.OUT)
    rtc = RTC()
    boot_btn = Pin(0, Pin.IN, Pin.PULL_DOWN)
    i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
    display = oled.Display_I2C(C.OLED_WIDTH, C.OLED_HEIGHT, i2c)
    soil_adc = ADC(Pin(34), atten=ADC.ATTN_11DB)
    ldr_adc = ADC(Pin(35), atten=ADC.ATTN_11DB)
except:
    print('Unable to initialize sensors')

d = DisplayHelper(display)
d.fill(0)
d.hline(0, 12, 128, 2)
# /INIT -----------------------------------------------------------------------------

# FUNCTIONS -------------------------------------------------------------------------


def log(txt):
    if C.ENABLE_LOGS:
        print(txt)


def limit(value, limit):
    return limit if value > limit else value


def handle_exception(exc: Exception):
    exc_as_str = str(exc)
    log(exc_as_str)
    for i, w in enumerate(exc_as_str.split(' ')):
        d.text_line(w, i + 3)
# /FUNCTIONS ------------------------------------------------------------------------


ldr = sensors.LdrSensor(ldr_adc)
soil = sensors.SoilSensor(soil_adc)
initial_time = time.time()


def data_pusher_thread(latest_request):
    wlan = WLAN(network)
    wlan.config(reconnects=5)

    def try_connect(retries=1, led=None):
        retry_count = 0
        # While network is available
        #   and has remaining retries
        while retry_count < retries and not wlan.isconnected() and wlan_client.is_nearby(wlan, C.SSID):
            d.text_line("Connecting...", 8)
            wlan_client.connect_to(
                wlan, C.SSID, C.PSSW, indicator_gpio=led)
            retry_count += 1
        d.clear_lines([8])
        # Check if connection succeded after retries
        return wlan.isconnected()

    def create_document(data: dict):
        fields = {}
        for key, value in data.items():
            valueType = 'Value'
            if re.match('^\w+\:\w+$', key):
                keyParts = str(key).split(':')
                valueType = keyParts[1] + valueType
                fields[keyParts[0]] = {valueType: value}
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
                fields[key] = {valueType: create_document(value)}
                continue
            fields[key] = {valueType: value}
        return {'fields': fields}

    def post_sensors_data(data):
        response = urequests.post(
            f'https://firestore.googleapis.com/v1/projects/{C.FIRESTORE_PROJECT_ID}/databases/(default)/documents/sensors',
            json=data,
            headers={
                'Content-Type': 'application/json',
                'key': C.FIRESTORE_API_KEY
            },
        )
        if response.json().get('error') is not None:
            raise 'Data error'
        return response

    while True:
        now = time.time()
        elapsed_time = now - latest_request
        try:
            if not try_connect(C.MAX_RECONNECTS, builtin_led):
                builtin_led.off()
                d.text_line("Not connected...", 8)
                log("Failed to reconnect...")
            elif elapsed_time >= C.SEND_REQUEST_SECS:
                log("Sending data...")
                d.text_line("Sending data...", 8)
                current_time = remote_time.get_current_time(
                    C.TIMEZONE).get('datetime')
                documentData = create_document({
                    'ldr': ldr.as_dict(),
                    'soil': soil.as_dict(),
                    'created_at:timestamp': current_time
                })
                post_sensors_data(documentData).close()
                log(documentData)
                d.clear_lines([8])
                latest_request = now
            time.sleep(1)
        except Exception as exc:
            err = str(exc)
            elapsed_time = 0
            log(err)
            d.text_line(err, 8)
            time.sleep(3)


def sensor_monitor_thread():
    button_released = True
    current_workflow = C.MONITOR_WORKFLOW

    def is_pressed(btn):
        return not btn.value()

    def show_calibration_menu(sensors: list):
        log("Calibration menu")
        d.text_line('Calibration', 1)
        for s in sensors:
            d.text_line('> Light', 3)
            d.text_line('  Soil', 4)

    def show_min_sensor_calibration(sensor: sensors.AnalogSensor):
        log(f'Voltaje: {sensor.read_voltage()/sensors.MICRO_VOLT}')
        log(f"{sensor.name} - Minimun")
        d.text_line(f"{sensor.name} - Minimun", 1)
        d.clear_lines([2])
        d.text_line(
            f'Voltaje: {sensor.read_voltage()/sensors.MICRO_VOLT}', 3)

    def show_max_sensor_calibration(sensor: sensors.AnalogSensor):
        log(f"{sensor.name} - Maximum")
        log(f'Voltaje: {sensor.read_voltage()/sensors.MICRO_VOLT}')
        d.text_line(f"{sensor.name} - Maximum", 1)
        d.clear_lines([2])
        d.text_line(
            f'Voltaje: {sensor.read_voltage()/sensors.MICRO_VOLT}', 3)

    def progress_bar(x, line, max_width, percent):
        y = (line - 1) * 8
        w = limit(percent, 100) * max_width // 100
        h = 6
        print({'p': percent, 'w': w})
        d.rect(x, y, max_width, h, 0, True)
        d.rect(x, y, max_width, h, 1)
        d.rect(x, y, int(w), h, 1, True)

    def display_sensors(sensors: dict):
        out = []
        for i, sen in enumerate(sensors.values()):
            out.append(f"{str(sen.get('name'))[0]}: {sen['values']}")
            d.text(f"{str(sen.get('name'))[0]}", 0, (i+2)*8)
            progress_bar(16, i+3, 100, sen['values']['percent'])
        log(", ".join(out))

    while True:
        if is_pressed(boot_btn):
            # REDIRECT TO CALIBRATION MENU
            d.fill(0)
            if current_workflow is C.MONITOR_WORKFLOW and button_released:
                current_workflow = C.CALIBRATION_MENU_WORKFLOW
            # REDIRECT TO SENSOR MIN VALUE CALIBRATION
            elif current_workflow is C.CALIBRATION_MENU_WORKFLOW and button_released:
                current_workflow = C.SET_SENSOR_MIN_CALIBRATION_VALUE
            # REDIRECT TO SENSOR MAX VALUE CALIBRATION
            elif current_workflow is C.SET_SENSOR_MIN_CALIBRATION_VALUE and button_released:
                soil.min_value = soil.read_voltage()
                current_workflow = C.SET_SENSOR_MAX_CALIBRATION_VALUE
            # END CALIBRATION AND REDIRECT TO MAIN WORKFLOW
            elif current_workflow is C.SET_SENSOR_MAX_CALIBRATION_VALUE and button_released:
                soil.max_value = soil.read_voltage()
                current_workflow = C.MONITOR_WORKFLOW
                d.clear_lines([3, 4])

            button_released = False

        elif not button_released:
            button_released = True

        if current_workflow is C.MONITOR_WORKFLOW:
            d.text_line("Plantagotchi", 1)
            display_sensors({
                'ldr': ldr.as_dict(),
                'soil': soil.as_dict()
            })
            time.sleep(1)
        elif current_workflow is C.CALIBRATION_MENU_WORKFLOW:
            show_calibration_menu([soil])
            time.sleep_ms(250)
        elif current_workflow is C.SET_SENSOR_MIN_CALIBRATION_VALUE:
            show_min_sensor_calibration(soil)
            time.sleep_ms(250)
        elif current_workflow is C.SET_SENSOR_MAX_CALIBRATION_VALUE:
            show_max_sensor_calibration(soil)
            time.sleep_ms(250)

# _thread.start_new_thread(data_pusher_thread, (initial_time,))
# _thread.start_new_thread(sensor_monitor_thread, ())
