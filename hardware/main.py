import time

import network
from machine import ADC, Pin, SoftI2C, RTC

import constants as Const
from lib import wlan_client, oled_display as oled
from workflows import monitor, calibration
# from dht11 import DHT11

# INITIALIZE PERIPHERALS ############################################################
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
# ###################################################################################

current_time = time.time()
current_workflow = 'MONITOR'
peripherals = {
    'rtc': rtc,
    'builtin_led': builtin_led,
    'oled': display,
    'ldr_adc': ldr_adc,
    'soil_adc': soil_adc,
    'button': boot_btn
}

monitorWorkflow = monitor.Workflow(peripherals, current_time)
calibrationWorkflow = calibration.Workflow(peripherals)

def handle_exception(self, exc: Exception):
    exc_as_str = str(exc)
    print(exc_as_str)
    for i, w in enumerate(exc_as_str.split(' ')):
        self.oled.text_line(w, i + 3)

while True:
    display.text_line(Const.PROJECT_NAME, 1)
    display.hline(0, 12 ,128, 2)

    try:
        if not boot_btn.value(): # values are inverted
            current_workflow = 'CALIBRATION'

        if current_workflow == 'MONITOR':
            monitorWorkflow.run()
        elif current_workflow == 'CALIBRATION':
            calibrationWorkflow.run()

        time.sleep_ms(100)

    except Exception as exc:
        handle_exception(exc)
        time.sleep(5)
        display.clear_lines(range(1, 9))