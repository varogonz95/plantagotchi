MICRO_VOLT= 1000000

class Sensor:
    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description
        self.max_value = 0
        self.min_value = 0

    @property
    def display_value(self) -> str:
        return None

    @property
    def is_calibrated(self) -> bool:
        return not self.max_value == self.min_value

    def read_computed(self):
        pass

    def read_adc(self):
        pass

    def read_voltage(self):
        pass

    def read_percent(self):
        pass

    def as_dict(self) -> dict:
        return {
            'name': self.name,
            'description': self.description,
            'values': {
                'adc': self.read_adc(),
                'display': self.display_value,
                'voltage': self.read_voltage(),
                'percent': self.read_percent(),
                'computed': self.read_computed()
            }
        }

class LdrSensor(Sensor):
    def __init__(self, ldr_sensor) -> None:
        super().__init__('Light', 'Light')
        self.__hw_sensor = ldr_sensor

    @property
    def display_value(self) -> str:
        return f'{"%.2f" % self.read_percent()}%'

    def read_computed(self):
        return 1 - (self.read_adc() / 4095)

    def read_adc(self):
        return self.__hw_sensor.read()

    def read_percent(self):
        return self.read_computed() * 100

    def read_voltage(self):
        return self.__hw_sensor.read_uv()

class SoilSensor(Sensor):
    def __init__(self, soil_sensor) -> None:
        super().__init__('Soil', 'Soil Moisture')
        self.__hw_sensor = soil_sensor

    @property
    def display_value(self) -> str:
        if self.is_calibrated:
            return f'{"%.2f" % (self.read_computed() * 100)}%'
        return 'N/A'

    def read_computed(self):
        v_delta = None
        l_delta = None
        if self.max_value < self.min_value:
            v_delta = self.read_voltage() - self.max_value
            l_delta = self.max_value - self.min_value
        elif self.min_value == self.max_value:
            v_delta = 1
            l_delta = 1
        else:
            v_delta = self.read_voltage() - self.min_value
            l_delta = self.min_value - self.max_value
        return v_delta/l_delta

    def read_adc(self):
        return self.__hw_sensor.read()

    def read_percent(self):
        return self.read_computed() * 100

    def read_voltage(self):
        return self.__hw_sensor.read_uv()
        
    def as_dict(self) -> dict:
        out = super().as_dict()
        out['values']['computed'] = self.read_computed() if self.is_calibrated else 0
        return out