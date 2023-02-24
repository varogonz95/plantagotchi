from lib import oled_display


class DisplayHelper:
    def __init__(self, display=oled_display.Display_I2C) -> None:
        self.display = display

    def fill(self, val):
        if self.display is not None:
            self.display.fill(val)

    def hline(self, x, y, w, h):
        if self.display is not None:
            self.display.hline(x, y, w, h)

    def rect(self, x, y, w, h, c, f=False):
        if self.display is not None:
            self.display.rect(x, y, w, h, c, f)

    def text(self, text: str, x, y):
        if self.display is not None:
            self.display.text(text, x, y)

    def text_line(self, text: str, line: int, vspan=1, overwrite=True, show=True):
        if self.display is not None:
            self.display.text_line(text, line, vspan, overwrite, show)

    def clear_lines(self, lines: list):
        if self.display is not None:
            self.display.clear_lines(lines)
