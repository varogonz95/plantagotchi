MICRO_VOLT = 1000000


class AnalogSensor:
    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description
        self.max_value = 0
        self.min_value = 0

    @property
    def display_value(self) -> str:
        return ''

    @property
    def is_calibrated(self) -> bool:
        return not self.max_value == self.min_value

    def read_computed(self):
        pass

    def read_adc(self) -> float:
        return 0

    def read_voltage(self) -> float:
        return 0

    def read_percent(self) -> float:
        return 0

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


class LdrSensor(AnalogSensor):
    def __init__(self, ldr_sensor) -> None:
        super().__init__('Light', 'Light')
        self.__hw_sensor = ldr_sensor

    @property
    def display_value(self) -> str:
        return f'{"%.2f" % self.read_percent()}%'

    def read_computed(self):
        return 1 - (self.read_adc() / 4095)
asds
    def read_adc(self):
        return self.__hw_sensor.read()

    def read_percent(self):
        return self.read_computed() * 100

    def read_voltage(self):
        return self.__hw_sensor.read_uv()


class SoilSensor(AnalogSensor):
    def __init__(self, soil_sensor) -> None:
        super().__init__('Soil', 'Soil Moisture')
        self.__hw_sensor = soil_sensor

    @property
    def display_value(self) -> str:
        if self.is_calibrated or self.__hw_sensor is not None:
            return f'{"%.2f" % (self.read_computed() * 100)}%'
        return 'N/A'

    def read_computed(self):
        if self.__hw_sensor is not None:
            v_adj = None
            v_delta = None
            if self.max_value < self.min_value:
                v_adj = self.read_voltage() - self.min_value
                v_delta = self.max_value - self.min_value
            elif self.min_value == self.max_value:
                v_delta = 1
                v_adj = 1
            else:
                v_adj = self.read_voltage() - self.min_value
                v_delta = self.min_value - self.max_value
            return v_adj/v_delta
        return 0

    def read_adc(self):
        return self.__hw_sensor.read() \
            if self.__hw_sensor is not None \
            else -1

    def read_percent(self):
        return self.read_computed() * 100

    def read_voltage(self):
        return self.__hw_sensor.read_uv() \
            if self.__hw_sensor is not None \
            else -1

    def as_dict(self) -> dict:
        out = super().as_dict()
        out['values']['computed'] = self.read_computed() \
            if self.is_calibrated else 0
        return out
