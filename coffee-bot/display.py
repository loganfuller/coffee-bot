import os
import atexit

import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw


PADDING = 1
LINE_HEIGHT = 10


class Display(object):
    def __init__(self):

        # 128x64 display with hardware SPI:
        self._disp = Adafruit_SSD1306.SSD1306_128_64(rst=24)

        # Initialize library.
        self._disp.begin()

        # Load default font.
        self._font = ImageFont.load_default()

        # Get display width and height.
        self.width = self._disp.width
        self.height = self._disp.height

        # Clear display.
        self._disp.clear()
        self._disp.display()

        # Create image buffer.
        # Make sure to create image with mode '1' for 1-bit color.
        self._image = Image.new("1", (self.width, self.height))

        # Create drawing object.
        self._draw = ImageDraw.Draw(self._image)

        atexit.register(self._exit_handler)

    def _exit_handler(self):
        # Power off display on exit
        self._disp.command(Adafruit_SSD1306.SSD1306_DISPLAYOFF)

    def _split_text_into_lines(self, text):
        lines = []
        curLine = ""
        cumWidth = 0

        for i, c in enumerate(text):
            char_width, char_height = self._draw.textsize(c, font=self._font)

            if (cumWidth + char_width) < (self.width - PADDING * 2):
                curLine += c
                cumWidth += char_width
            else:
                lines.append(curLine)
                curLine = c
                cumWidth = 0

        if curLine:
            lines.append(curLine)

        return lines

    def show_text(self, text=""):
        """Display text. Method accepts strings or lists of strings. Text will
        be wrapped to fit within screen bounds.
        """

        # Clear image buffer by drawing a black filled box.
        self._draw.rectangle((0, 0, self.width, self.height), outline=0,
                             fill=0)

        if type(text) is str:
            text = [text]

        vert_spacing = 0
        for line in text:
            for i, split_line in enumerate(self._split_text_into_lines(line)):
                self._draw.text((PADDING, PADDING + vert_spacing),
                                split_line, font=self._font, fill=255)
                vert_spacing += LINE_HEIGHT

        # Draw the image buffer.
        self._disp.image(self._image)
        self._disp.display()
