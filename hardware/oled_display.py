from ssd1306 import SSD1306_I2C

MEM_SIZE = 8

class OLEDDisplay_I2C(SSD1306_I2C):

    def __init__(self, width, height, i2c, addr=0x3C, external_vcc=False):
        self.width = width
        self.height = height
        super().__init__(width, height, i2c, addr, external_vcc)

    def text_line(self, text: str, line: int, vspan = 1, overwrite = True, show=True):
        h = MEM_SIZE
        y = ((line - 1) * MEM_SIZE) + vspan
        w = self.width
        if overwrite:
            super().fill_rect(0, y, w, h, 0)
        super().text(text, 0, y, 1)
        if show:
            super().show()

    def clear_line(self, line: int):
        h = MEM_SIZE
        y = ((line - 1) * MEM_SIZE)
        w = self.width
        super().fill_rect(0, y, w, h, 0)