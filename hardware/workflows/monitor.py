import time
import urequests

import constants as Const
from lib import wlan_client, remote_time, app_sensors as sensors

class Workflow:

    def __init__(self, peripherals: dict, start_time: tuple):
        self.__latest_sent_request_time = start_time
        self.rtc = peripherals.get('rtc')
        self.builtin_led = peripherals.get('builtin_led')
        self.oled = peripherals.get('oled')
        self.ldr = sensors.LdrSensor(peripherals.get('ldr_adc'))
        self.soil = sensors.SoilSensor(peripherals.get('soil_adc'))
        self.wlan = peripherals.get('wlan')

    def __create_document(self, data: dict):
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
                fields[key] = { valueType: self.create_document(value) }
                continue

            fields[key] = { valueType: value }
        
        return {'fields': fields}

    def __display_sensors(self, sensors: dict):
        for i, value in enumerate(sensors.values()):
            print(f"{value.get('name')}: {value.get('raw_value')}")
            self.oled.text_line(f"{value.get('name')}: {value.get('display_value')}", i+3)

    def __post_sensors_data(self, data) -> urequests.Response:
        return urequests.post(
            f'https://firestore.googleapis.com/v1/projects/{Const.FIRESTORE_PROJECT_ID}/databases/(default)/documents/sensors',
            json=data,
            headers={
                'Content-Type': 'application/json',
                'key': Const.FIRESTORE_API_KEY
            },
        )

    def __try_connect(self, retries = 1, led = None):
        retry_count = 0
        # While network is available
        #   and has remaining retries
        while retry_count < retries and not self.wlan.isconnected() and wlan_client.is_nearby(self.wlan, Const.SSID):
            self.oled.text_line("Connecting...", 8)
            wlan_client.connect(self.wlan, Const.SSID, Const.PSSW, indicator_gpio = led)
            retry_count += 1

        # Check if connection succeded after retries
        return self.wlan.isconnected()

    def run(self):
        sensors_data: dict = {
            'ldr': self.ldr.as_dict(),
            'soil': self.soil.as_dict()
        }
        
        now = time.time()
        elapsed_secs_since_latest_request = now - self.__latest_sent_request_time

        self.__display_sensors(sensors_data)
        # if not self.__try_connect(Const.MAX_RECONNECTS, self.builtin_led):
        #     self.builtin_led.off()
        #     self.oled.text_line("Not connected...", 8)
        #     print("Failed to reconnect...")
        # elif elapsed_secs_since_latest_request >= Const.SEND_REQUEST_SECS:
        #     print("Sending data...")
        #     self.__latest_sent_request_time = now
        #     self.oled.text_line("Sending data...", 8)
        #     documentData = self.__create_document(sensors_data)
        #     current_time = remote_time.get_current_time(Const.TIMEZONE).get('datetime')
        #     documentData['fields']['created_at'] = {'timestampValue': current_time}
        #     print(documentData)
        #     self.__post_sensors_data(documentData).close()
        #     self.oled.clear_lines([8])