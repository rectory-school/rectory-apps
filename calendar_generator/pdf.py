"""Calendar PDF generation"""

import os
from dataclasses import dataclass
from functools import cache, cached_property

from typing import List

from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from . import grids


def _register_fonts():
    current_path = os.path.dirname(os.path.realpath(__file__))
    font_folder = os.path.join(current_path, "fonts")

    for font_file in os.listdir(font_folder):
        font_name, extension = os.path.splitext(font_file)
        if (extension) == ".ttf":
            pdfmetrics.registerFont(TTFont(font_name, os.path.join(font_folder, font_file)))


_register_fonts()


@dataclass
class ColorSet:
    """This is it's own class so I can keep them around as presets"""

    title_color: colors.HexColor
    line_color: colors.HexColor
    inner_grid_color: colors.HexColor
    header_text_color: colors.HexColor
    date_color: colors.HexColor
    letter_color: colors.HexColor
    label_color: colors.HexColor

    divide_header: bool


@dataclass
class Layout:
    """Preset for a PDF size"""

    width: float
    height: float
    margins: float
    line_width: float

    title_font_size_override: float = 0  # 0 is auto-sized

    header_font_name: str = "HelveticaNeue-Bold"
    letter_font_name: str = "HelveticaNeue-Light"
    date_font_name: str = "HelveticaNeue-Light"
    title_font_name: str = "HelveticaNeue-Bold"

    x_pos: float = 0
    y_pos: float = 0

    header_pad: float = 1.5

    @property
    def outer_height(self) -> float:
        """The total height we have to fit everything into"""

        return self.height - self.margins * 2

    @property
    def outer_width(self) -> float:
        """The total width we have to fit everything into"""

        return self.width - self.margins * 2

    @property
    def left_offset(self) -> float:
        """Overall left position to start drawing at"""

        return self.margins + self.x_pos

    @property
    def bottom_offset(self) -> float:
        """Overall bottom position to start drawing at"""

        return self.margins + self.y_pos

    def font_size_for_title(self, title: str) -> float:
        """Get the font size for a given title"""

        if self.title_font_size_override:
            return self.title_font_size_override

        max_size = self.outer_width * .5

        return get_maximum_width(title, max_size, self.title_font_name)

    def subdivide(self, row_count: int, col_count: int) -> List['Layout']:
        """Subdivide will give back a bunch of sub-layouts for drawing multiple calendars on one page,
        starting in the top left and in reading order"""

        col_pad = self.margins
        row_pad = self.margins / 2

        out = []

        # The column width is how wide each calendar should be drawn with 0 margins
        # Overall, we have the total of the inner width of the page minus the width that each column will take up
        space_for_cols = self.outer_width - (col_pad * (col_count-1))
        col_width = space_for_cols / col_count

        space_for_rows = self.outer_height - (row_pad * (row_count - 1))
        row_height = space_for_rows / row_count

        for row_index in range(row_count):
            # We're indexing from the top but drawing from the bottom, so this has to do some inversion
            row_offset = self.outer_height - row_height * (row_index+1) - row_pad * row_index + self.margins

            for col_index in range(col_count):
                col_offset = self.margins + col_index * (col_width + col_pad)

                layout = Layout(width=col_width, height=row_height,
                                line_width=self.line_width,
                                margins=0,
                                x_pos=col_offset, y_pos=row_offset)

                out.append(layout)

        return out


@dataclass
class CalendarGenerator:
    """A calendar generator draws a calendar on a canvas"""

    canvas: canvas.Canvas
    grid: grids.CalendarGrid

    color_set: ColorSet
    layout: Layout

    minimum_row_count_calculation: float = 0

    def draw(self):
        """Execute the actual draw"""

        self._draw_title()
        self._draw_frame_background()
        self._draw_header()
        self._draw_grid()
        self._draw_dates()
        self._draw_letters()

    def _draw_title(self):
        decent = get_decent(self.layout.title_font_name, self._title_font_size)
        y_pos = self.layout.bottom_offset + self._total_grid_height - decent

        self.canvas.setFont(self.layout.title_font_name, self._title_font_size)
        self.canvas.setFillColor(self.color_set.title_color)

        self.canvas.drawString(self.layout.left_offset, y_pos, self.grid.title)

    def _draw_frame_background(self):
        """Draw the frame background"""

        self.canvas.setFillColor(self.color_set.line_color)
        self.canvas.rect(self.layout.left_offset,
                         self.layout.bottom_offset,
                         self.layout.outer_width,
                         self._total_grid_height,
                         stroke=0, fill=1)

    def _draw_header(self):
        self.canvas.setFillColor(self.color_set.header_text_color)
        self.canvas.setStrokeColor(self.color_set.inner_grid_color)
        self.canvas.setFont(self.layout.header_font_name, self._header_font_size)
        self.canvas.setLineWidth(self.layout.line_width)

        # Default padding is 120%, so .1 is half of the padding margin
        _, descent = pdfmetrics.getAscentDescent(self.layout.header_font_name, self._header_font_size)
        y_pos = self.layout.bottom_offset + self._grid_height + (
            self._header_height - self._header_font_size)/2 - descent

        left = self.layout.left_offset + self.layout.line_width

        for i, header in enumerate(self.grid.headers):
            center = left + self._column_width / 2

            self.canvas.drawCentredString(center, y_pos, header)

            if self.color_set.divide_header and i > 0:
                bottom = self.layout.bottom_offset + self._grid_height
                top = bottom + self._header_height

                x_pos = left - self.layout.line_width / 2
                self.canvas.line(x_pos, bottom, x_pos, top)

            left += self._column_width
            left += self.layout.line_width

    def _draw_grid(self):
        self.canvas.setFillColor(self.color_set.inner_grid_color)

        bottom = self.layout.bottom_offset + self.layout.line_width
        for _ in range(self._row_count):
            left = self.layout.left_offset + self.layout.line_width

            for _ in range(self._column_count):
                self.canvas.rect(left, bottom, self._column_width, self._row_height, stroke=0, fill=1)
                left += self._column_width
                left += self.layout.line_width

            bottom += self._row_height
            bottom += self.layout.line_width

    def _draw_letters(self):
        # Note, this calculation grabs the top, but I'm subtracting the
        # row height and line before using it, so it becomes the bottom
        # as soon as the first row is entered
        bottom = self.layout.bottom_offset + self._grid_height + self.layout.line_width

        for row in self.grid.grid:
            # Just like in the rows, I'm shifting left a column
            # because the first column adds it before doing anything
            left = self.layout.left_offset - self._column_width

            bottom -= self._row_height
            bottom -= self.layout.line_width

            for col in row:
                left += self.layout.line_width
                left += self._column_width

                if not col:
                    continue

                center = left + self._column_width / 2

                # This gets defined up here because the letter calculations will use it
                # to adjust their positions
                label_font_size = 0

                if col.label:
                    maximum_font_size = get_maximum_width(col.label, self._column_width*.9,
                                                          self.layout.letter_font_name)
                    label_font_size = min(maximum_font_size, self._row_height/3)

                    descent = get_decent(self.layout.letter_font_name, label_font_size)
                    y_pos = bottom - descent

                    self.canvas.setFont(self.layout.letter_font_name, label_font_size)
                    self.canvas.setFillColor(self.color_set.label_color)
                    self.canvas.drawCentredString(center, y_pos, col.label)

                if col.letter:
                    letter_font_size = self._letter_font_size

                    if label_font_size:
                        letter_font_size = min(self._letter_font_size, self._row_height - label_font_size)

                    self.canvas.setFont(self.layout.letter_font_name, letter_font_size)
                    self.canvas.setFillColor(self.color_set.letter_color)

                    x_pos = left + self._column_width * 0.05
                    y_pos = bottom + self._row_height * .1 + label_font_size

                    self.canvas.drawString(x_pos, y_pos, col.letter)

    def _draw_dates(self):
        self.canvas.setFillColor(self.color_set.date_color)
        self.canvas.setFont(self.layout.date_font_name, self._date_font_size)

        _, descent = pdfmetrics.getAscentDescent(self.layout.date_font_name, self._date_font_size)

        top = self.layout.bottom_offset + self._grid_height
        top -= self._date_font_size
        top -= descent

        for row in self.grid.grid:
            right = self.layout.left_offset + self.layout.line_width + self._column_width - self._column_width*.025

            for col in row:
                if col:
                    self.canvas.drawRightString(right, top, str(col.date.day))

                right += self.layout.line_width
                right += self._column_width

            top -= self.layout.line_width
            top -= self._row_height

    @cached_property
    def _column_width(self) -> float:
        """Determine the inner width of each column"""

        width = self.layout.outer_width
        width -= self.layout.line_width * (self._column_count + 1)
        return width / self._column_count

    @cached_property
    def _row_height(self) -> float:
        """Determine the inner height of each row"""

        height = self.layout.outer_height
        height -= self._title_space_used
        height -= self._header_height
        height -= self.layout.line_width * self._row_count

        return height / self._row_count

    @cached_property
    def _column_count(self):
        return len(self.grid.headers)

    @cached_property
    def _row_count(self):
        return len(self.grid.grid)

    @cached_property
    def _title_font_size(self) -> float:
        return self.layout.font_size_for_title(self.grid.title)

    @cached_property
    def _title_space_used(self) -> float:
        """The total space used by the title"""

        return self._title_font_size

    @cached_property
    def _total_grid_height(self) -> float:
        """The height available for the grid and headers"""

        return self.layout.outer_height - self._title_space_used

    @cached_property
    def _header_font_size(self) -> float:
        """The calculated size of the headers"""

        maximum_width = self._column_width * .8

        if self.color_set.divide_header:
            maximum_width -= self.layout.line_width

        current_size = self._column_width  # Set an upper bound to keep the column header at most squarish

        for header in self.grid.headers:
            possible_size = get_maximum_width(header, maximum_width, self.layout.header_font_name)
            if possible_size < current_size:
                current_size = possible_size

        return current_size

    @cached_property
    def _header_height(self) -> float:
        """The height used by the headers"""

        return self.layout.header_pad * self._header_font_size

    @cached_property
    def _date_font_size(self) -> float:
        all_dates = set()

        for row in self.grid.grid:
            for col in row:
                if col and col.date:
                    all_dates.add(str(col.date.day))

        all_letters = set()
        for row in self.grid.grid:
            for col in row:
                if col and col.letter:
                    all_letters.add(col.letter)

        letter_widths = (stringWidth(letter, self.layout.letter_font_name, self._letter_font_size)
                         for letter in all_letters)
        max_letter_width = max(*letter_widths)

        # Allow up to the lesser of half the cell, or 60% of the remaining space
        space_available = min((self._column_width - max_letter_width)*.6, self._column_width / 2)
        max_day_widths = (get_maximum_width(day, space_available, self.layout.date_font_name)
                          for day in all_dates if day)

        theoretical_max = min(*max_day_widths)

        # Allow either the width-based max from above, or half the cell height
        return min(theoretical_max, (self.layout.outer_height / len(self.grid.grid)) * .5)

    @cached_property
    def _letter_font_size(self) -> float:
        all_letters = set()

        for row in self.grid.grid:
            for col in row:
                if col and col.letter:
                    all_letters.add(col.letter)

        # Letters get 80% of the cell
        maximum_width = self._column_width * .8

        # Maximum of 80% of the row height, if we have a really weirdly shaped calendar here
        current_size = self._row_height
        for letter in all_letters:
            possible_size = get_maximum_width(letter, maximum_width, self.layout.date_font_name)

            if possible_size < current_size:
                current_size = possible_size

        return current_size

    @cached_property
    def _grid_height(self) -> float:
        """The height of the internal grid"""

        return self._total_grid_height - self._header_height


@cache
def get_maximum_width(text: str, maximum: float, font: str) -> float:
    """Get the maximum font size to fit some given text into a given width"""

    font_size = 12
    width = stringWidth(text, font, font_size)
    return maximum/width * font_size


@cache
def get_decent(font_name, font_size) -> float:
    """Get the descent for some font at some size"""

    _, descent = pdfmetrics.getAscentDescent(font_name, font_size)
    return descent
