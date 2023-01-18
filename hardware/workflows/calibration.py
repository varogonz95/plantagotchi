import time
import constants as Const
from lib import oled_display as oled, app_sensors as sensors

class Workflow:
    
    def __init__(self, peripherals: dict):
        self.builtin_led = peripherals.get('builtin_led')
        self.oled: oled.Display_I2C = peripherals.get('oled')
        self.ldr = sensors.LdrSensor(peripherals.get('ldr_adc'))
        self.soil = sensors.SoilSensor(peripherals.get('soil_adc'))
        self.button = peripherals.get('button')

        self.__sensors = [self.soil, self.ldr]
        self.__exit = False

    def run(self):
        self.oled.text_line('Calibration Menu', 1)
        self.oled.hline(0, 12 ,128, 2)
        
        for s in enumerate(self.__sensors):
            print(f"{s}")
        print()

        while not self.exit:
            time.sleep(1)