import framebuf
from drivers.ssd1306 import SSD1306_I2C

MEM_SIZE = 8

class Display_I2C(SSD1306_I2C):

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

    def clear_lines(self, lines: list):
        h = MEM_SIZE
        w = self.width
        for i in lines:
            y = (i - 1) * MEM_SIZE
            super().fill_rect(0, y, w, h, 0)

    def image(self, filename, x, y):
        with open(filename, 'rb') as f:
            f.readline() # Magic number
            f.readline() # Creator comment
            f.readline() # Dimensions
            data = bytearray(f.read())
        buffer = framebuf.FrameBuffer(data, self.width, self.height, framebuf.MONO_HLSB)
        self.blit(buffer, x, y)