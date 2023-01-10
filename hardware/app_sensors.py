class Sensor:
    def __init__(self, description: str) -> None:
        self.description = description

    @property
    def display_value(self) -> str:
        return None

    def read(self):
        return None

    def as_dict(self) -> dict:
        result = self.__dict__
        result['raw_value'] = self.read()
        result['display_value'] = self.display_value
        return result

class LdrSensor(Sensor):
    def __init__(self, ldr_sensor) -> None:
        super().__init__('Light')
        self.__hw_sensor = ldr_sensor

    @property
    def display_value(self) -> str:
        return f'{"%.2f" % (100 - (20 * self.read() / 819))}%'

    def read(self):
        return self.__hw_sensor.read()

    def as_dict(self) -> dict:
        return {
            'description': self.description,
            'raw_value': self.read(),
            'display_value': self.display_value
        }

class SoilSensor(Sensor):
    def __init__(self, soil_sensor) -> None:
        super().__init__('Soil Moisture')
        self.__hw_sensor = soil_sensor

    @property
    def display_value(self) -> str:
        return f'{"%.2f" % (100 - (20 * self.read() / 819))}%'

    def read(self):
        return self.__hw_sensor.read()

    def as_dict(self) -> dict:
        return {
            'description': self.description,
            'raw_value': self.read(),
            'display_value': self.display_value
        }

class DHT11Sensor(Sensor):
    def __init__(self, dht11_sensor) -> None:
        super().__init__('Humidity & Temp')
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

    def as_dict(self) -> dict:
        return {
            'description': self.description,
            'raw_value': self.read(),
            'display_value': self.display_value
        }