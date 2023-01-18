MICRO_VOLT= 1000000
class Sensor:
    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description

    @property
    def display_value(self) -> str:
        return None

    def read(self):
        return None

    def as_dict(self) -> dict:
        return {
            'name': self.name,
            'description': self.description,
            'raw_value': self.read(),
            'display_value': self.display_value
        }

class LdrSensor(Sensor):
    def __init__(self, ldr_sensor) -> None:
        super().__init__('Light', 'Light')
        self.__hw_sensor = ldr_sensor

    @property
    def display_value(self) -> str:
        return f'{"%.2f" % (100 - (20 * self.read() / 819))}%'

    def read(self):
        return self.__hw_sensor.read()

class SoilSensor(Sensor):
    def __init__(self, soil_sensor) -> None:
        super().__init__('Soil', 'Soil Moisture')
        self.__hw_sensor = soil_sensor

    @property
    def display_value(self) -> str:
        # return f'{"%.2f" % ((20 * self.read() / 819))}%'
        return self.read()

    def read(self):
        return self.__hw_sensor.read_uv() / MICRO_VOLT

class DHT11Sensor(Sensor):
    def __init__(self, dht11_sensor) -> None:
        super().__init__('DHT11', 'Humidity & Temp')
        self.__hw_sensor = dht11_sensor

    @property
    def display_value(self) -> str:
        return f'{"%.2f" % (100 - (20 * self.read() / 819))}%'

    def read(self):
        return self.__hw_sensor.read()

    # def display_dht11_readings(dht11_sensor: DHT11, h_line, t_line):
    #     humidity = dht11_sensor.humidity()
    #     temp = dht11_sensor.temperature()
    #     oled.text_line(f'Humidity: {humidity}%', h_line)
    #     oled.text_line(f'Temp: {temp}C', t_line)