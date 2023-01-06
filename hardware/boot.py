# This file is executed on every boot (including wake-boot from deepsleep)
#import webrepl
#webrepl.start()

import esp

esp.osdebug(esp.LOG_VERBOSE)
import time

import ssd1306
from machine import Pin, SoftI2C

# using default address 0x3C
i2c = SoftI2C(sda=Pin(21), scl=Pin(22))
display = ssd1306.SSD1306_I2C(128, 64, i2c)
display.fill(0)
display.fill_rect(1, 16, 32, 32, 1)
display.fill_rect(3, 18, 28, 28, 0)
display.vline(10, 24, 22, 1)
display.vline(17, 18, 22, 1)
display.vline(24, 24, 22, 1)
display.fill_rect(28, 40, 2, 4, 1)
display.text('Alvaro', 40, 24, 1)
display.text('Gonzalez Q', 40, 38, 1)
display.text('Booting up...', 0, 54, 1)
display.show()

time.sleep(3)
display.poweroff()