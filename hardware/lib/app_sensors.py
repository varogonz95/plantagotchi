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

    def read(self):
        pass
        

    def read_adc(self):
        pass

    def read_voltage(self):
        pass

    def as_dict(self) -> dict:
        return {
            'name': self.name,
            'description': self.description,
            'values': {
                'adc': self.read_adc(),
                'display': self.display_value,
                'voltage': self.read_voltage(),
                'computed': self.read() if self.is_calibrated else 0
            }
        }

class LdrSensor(Sensor):
    def __init__(self, ldr_sensor) -> None:
        super().__init__('Light', 'Light')
        self.__hw_sensor = ldr_sensor

    @property
    def display_value(self) -> str:
        return f'{"%.2f" % (100 - (20 * self.read_adc() / 819))}%'

    def read_adc(self):
        return self.__hw_sensor.read()

    def read_voltage(self):
        return self.__hw_sensor.read_uv()

class SoilSensor(Sensor):
    def __init__(self, soil_sensor) -> None:
        super().__init__('Soil', 'Soil Moisture')
        self.__hw_sensor = soil_sensor

    @property
    def display_value(self) -> str:
        if self.is_calibrated:
            return f'{"%.2f" % (self.read() * 100)}%'
        return 'N/A'

    def read(self):
        if self.max_value < self.min_value:
            return (self.read_voltage() - self.min_value)/(self.max_value - self.min_value)
        else:
            return (self.read_voltage() - self.max_value)/(self.min_value - self.max_value)

    def read_adc(self):
        return self.__hw_sensor.read()

    def read_voltage(self):
        return self.__hw_sensor.read_uv()

class DHT11Sensor(Sensor):
    def __init__(self, dht11_sensor) -> None:
        super().__init__('DHT11', 'Humidity & Temp')
        self.__hw_sensor = dht11_sensor

    @property
    def display_value(self) -> str:
        return f'{"%.2f" % (100 - (20 * self.read_adc() / 819))}%'

    def read_adc(self):
        return self.__hw_sensor.read()

    # def display_dht11_readings(dht11_sensor: DHT11, h_line, t_line):
    #     humidity = dht11_sensor.humidity()
    #     temp = dht11_sensor.temperature()
    #     oled.text_line(f'Humidity: {humidity}%', h_line)
    #     oled.text_line(f'Temp: {temp}C', t_line)