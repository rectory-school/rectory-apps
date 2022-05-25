"""Calendar PDF generation"""

import os
from dataclasses import dataclass

from typing import Optional, List

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
class Style:
    """This is it's own class so I can keep them around as presets"""

    header_text_color: colors.HexColor
    letter_color: colors.HexColor
    date_color: colors.HexColor
    label_color: colors.HexColor

    title_color: Optional[colors.HexColor] = None

    outline_color: Optional[colors.HexColor] = None
    grid_line_color: Optional[colors.HexColor] = None
    header_divider_color: Optional[colors.HexColor] = None

    header_background_color: Optional[colors.HexColor] = None
    frame_background_color: Optional[colors.HexColor] = None

    header_divider_width: int = 1
    outline_width: int = 1
    grid_line_width: int = 1

    title_font_size: Optional[int] = None  # None or 0 is auto-sized

    header_font_name: str = "HelveticaNeue-Bold"
    letter_font_name: str = "HelveticaNeue-Light"
    date_font_name: str = "HelveticaNeue-Light"
    title_font_name: str = "HelveticaNeue-Bold"


@dataclass
class Layout:
    """Preset for a PDF size"""

    width: float
    height: float
    top_margin: float
    bottom_margin: float
    left_margin: float
    right_margin: float

    x_pos: float = 0
    y_pos: float = 0

    header_pad: float = 1.5

    @property
    def inner_height(self) -> float:
        """Calculate the inner height of the PDF"""

        return self.height - self.top_margin - self.bottom_margin

    @property
    def inner_width(self) -> float:
        """Calculate the inner width of the PDF"""

        return self.width - self.left_margin - self.right_margin

    @property
    def left_offset(self) -> float:
        """Overall left position to start drawing at"""

        return self.left_margin + self.x_pos

    @property
    def bottom_offset(self) -> float:
        """Overall bottom position to start drawing at"""

        return self.bottom_margin + self.y_pos

    def subdivide(self, row_count: int, col_count: int, row_pad: float, col_pad: float) -> List['Layout']:
        """Subdivide will give back a bunch of sub-styles for drawing multiple calendars on one page,
        starting in the top left and in reading order"""

        out = []

        # The column width is how wide each calendar should be drawn with 0 margins
        # Overall, we have the total of the inner width of the page minus the width that each column will take up
        space_for_cols = self.inner_width - (col_pad * (col_count-1))
        col_width = space_for_cols / col_count

        space_for_rows = self.inner_height - (row_pad * (row_count - 1))
        row_height = space_for_rows / row_count

        for row_index in range(row_count):
            # We're indexing from the top but drawing from the bottom, so this has to do some inversion
            row_offset = self.inner_height - row_height * (row_index+1) - row_pad * row_index + self.bottom_margin

            for col_index in range(col_count):
                col_offset = self.left_margin + col_index * (col_width + col_pad)

                style = Layout(width=col_width, height=row_height,
                               top_margin=0, bottom_margin=0,
                               left_margin=0, right_margin=0,
                               x_pos=col_offset, y_pos=row_offset)

                out.append(style)

        return out


@dataclass
class CalendarGenerator:
    """A calendar generator draws a calendar on a canvas"""

    canvas: canvas.Canvas
    grid: grids.CalendarGrid

    style: Style
    layout: Layout

    minimum_row_count_calculation: float = 0

    _title_font_size: float = None
    _header_font_size: float = None
    _date_font_size: float = None
    _default_letter_font_size: float = None
    _y_pos_below_header: float = None
    _row_height: float = None
    _header_height: float = None

    def draw(self):
        """Execute the actual draw"""

        self._calculate_internals()

        self._draw_title()
        self._draw_frame()
        self._draw_header()
        self._draw_grid()
        self._draw_dates()
        self._draw_letters()

    def _draw_title(self):
        if not self.style.title_color:
            return

        _, descent = pdfmetrics.getAscentDescent(self.style.title_font_name, self._title_font_size)

        y_pos = self._y_pos_below_header + self._header_height - descent

        self.canvas.setFont(self.style.title_font_name, self._title_font_size)
        self.canvas.setFillColor(self.style.title_color)

        self.canvas.drawString(self.layout.left_offset, y_pos, self.grid.title)

    def _draw_frame(self):
        if not(self.style.frame_background_color
               or (self.style.outline_width and self.style.outline_color)):
            return

        draw_stroke = 0
        draw_fill = 0

        x_pos = self.layout.left_offset
        y_pos = self._y_pos_below_header - self._row_height * len(self.grid.grid)

        width = self.layout.inner_width
        height = self._row_height * len(self.grid.grid) + self._header_height

        # Draw the bounding box
        if self.style.outline_width and self.style.outline_color:
            draw_stroke = 1

            # We have to do this manually instead of with the internal calculators
            # because we are the one that modifies it,
            # and we are trying to draw on the line
            x_pos += self.style.outline_width/2
            y_pos += self.style.outline_width/2

            width = width - self.style.outline_width
            height = height - self.style.outline_width

            self.canvas.setLineWidth(self.style.outline_width)
            self.canvas.setStrokeColor(self.style.outline_color)

        if self.style.frame_background_color:
            draw_fill = 1

            self.canvas.setFillColor(self.style.frame_background_color)

        self.canvas.rect(x_pos, y_pos, width, height, stroke=draw_stroke, fill=draw_fill)

    def _draw_header(self):
        header_width = self._internal_width / len(self.grid.headers)

        # Draw the header background
        if self.style.header_background_color:
            x_pos = self._x_position
            y_pos = self._y_pos_below_header

            self.canvas.setFillColor(self.style.header_background_color)
            self.canvas.rect(x_pos, y_pos, self._internal_width, self._header_height, stroke=0, fill=1)

        # Draw the text elements
        self.canvas.setFillColor(self.style.header_text_color)
        self.canvas.setFont(self.style.header_font_name, self._header_font_size)

        for i, header in enumerate(self.grid.headers):
            x_pos = self._x_position + header_width/2 + header_width * i

            # Default padding is 120%, so .1 is half of the padding margin
            _, descent = pdfmetrics.getAscentDescent(self.style.header_font_name, self._header_font_size)

            y_pos = self._y_pos_below_header - descent + (self._header_height - self._header_font_size) / 2

            self.canvas.drawCentredString(x_pos, y_pos, header)

        # Draw the lines between each header
        if self.style.header_divider_color:
            self.canvas.setStrokeColor(self.style.header_divider_color)
            bottom = self._y_pos_below_header - self.style.grid_line_width / 2
            top = bottom + self._header_height
            if self.style.outline_width and self.style.outline_color:
                top -= self.style.outline_width / 2

            self.canvas.setLineWidth(self.style.header_divider_width)

            for i in range(len(self.grid.headers)):
                # Don't draw a line on the left page border
                if i == 0:
                    continue

                x_pos = self._x_position + i*header_width - self.style.header_divider_width/2
                self.canvas.line(x_pos, bottom, x_pos, top)

    def _draw_grid(self):
        if not self.style.grid_line_color and not self.style.grid_line_width:
            return

        self.canvas.setLineWidth(self.style.grid_line_width)
        self.canvas.setStrokeColor(self.style.grid_line_color)

        for column_index in range(1, len(self.grid.headers)):
            x_pos = self._x_position + self._column_width * column_index - self.style.grid_line_width/2
            top = self._y_pos_below_header
            bottom = self._y_pos_below_header - len(self.grid.grid) * self._row_height

            self.canvas.line(x_pos, top, x_pos, bottom)

        for row_index in range(1, len(self.grid.grid)):
            left = self._x_position
            right = self._x_position + self._internal_width

            y_pos = self._y_pos_below_header - (self._row_height * row_index)

            self.canvas.line(left, y_pos, right, y_pos)

    def _draw_letters(self):
        if not self.style.letter_color:
            return

        _, default_letter_descent = pdfmetrics.getAscentDescent(self.style.letter_font_name,
                                                                self._default_letter_font_size)

        for row_index, row in enumerate(self.grid.grid):
            for col_index, col in enumerate(row):
                if not col:
                    continue

                label_font_size = 0

                if col.label:
                    center_at = self._x_position + (col_index)*self._column_width + self._column_width/2

                    label_font_size = min(get_font_size_maximum_width(col.label, self._column_width*.9,
                                                                      self.style.letter_font_name),
                                          self._row_height/3)

                    center_at = self._x_position + (col_index)*self._column_width + \
                        self._column_width/2

                    _, label_descent = pdfmetrics.getAscentDescent(self.style.letter_font_name, label_font_size)

                    label_y_pos = self._y_pos_below_header - label_font_size - (self._row_height * (row_index + 1)
                                                                                ) + label_font_size - label_descent

                    self.canvas.setFont(self.style.letter_font_name, label_font_size)
                    self.canvas.setFillColor(self.style.label_color)
                    self.canvas.drawCentredString(center_at, label_y_pos, col.label)

                if col.letter:
                    letter_font_size = self._default_letter_font_size
                    letter_descent = default_letter_descent

                    if label_font_size:
                        letter_font_size = min(self._default_letter_font_size, self._row_height - label_font_size)
                        _, letter_descent = pdfmetrics.getAscentDescent(self.style.letter_font_name,
                                                                        letter_font_size)

                    self.canvas.setFont(self.style.letter_font_name, letter_font_size)
                    self.canvas.setFillColor(self.style.letter_color)

                    # We have to get the right bound here, thus the +1, and pad it out, thus the - 5%
                    x_pos = self._x_position + (col_index)*self._column_width + self._column_width * 0.05
                    y_pos = self._y_pos_below_header - letter_font_size - (
                        self._row_height * row_index) - letter_descent / 2

                    self.canvas.drawString(x_pos, y_pos, col.letter)

    def _draw_dates(self):
        if not self.style.date_color:
            return

        self.canvas.setFillColor(self.style.date_color)
        self.canvas.setFont(self.style.date_font_name, self._date_font_size)

        _, descent = pdfmetrics.getAscentDescent(self.style.date_font_name, self._date_font_size)

        for row_index, row in enumerate(self.grid.grid):
            y_pos = self._y_pos_below_header - self._date_font_size - self._row_height*row_index - descent

            for col_index, col in enumerate(row):
                if not col or not col.date:
                    continue

                # We have to get the right bound here, thus the +1, and pad it out, thus the - 5%
                x_pos = self._x_position + (col_index+1)*self._column_width - self._column_width * 0.05
                self.canvas.drawRightString(x_pos, y_pos, str(col.date.day))

    @property
    def _column_width(self) -> float:
        """Determine the width of each column"""

        return float(self._internal_width) / len(self.grid.headers)

    @property
    def _x_position(self) -> float:
        """The X position that we can start drawing at, given frames and such"""

        if self.style.outline_width and self.style.outline_color:

            # Don't divide by 2 because we're pushing the line so it's fully enclosed within the width
            return self.layout.left_offset + self.style.outline_width

        return self.layout.left_offset

    @property
    def _internal_width(self) -> float:
        """The internally accessible width, given frames and such"""

        if self.style.outline_width and self.style.outline_color:
            # The line is pushed fully within the bounding box, so take both sides of it into account

            return self.layout.inner_width - self.style.outline_width*2

        return self.layout.inner_width

    def _set_title_font_size(self) -> float:
        if self.style.title_font_size:
            self._title_font_size = self.style.title_font_size
            return

        max_size = self.layout.inner_width * .5

        self._title_font_size = get_font_size_maximum_width(self.grid.title, max_size, self.style.title_font_name)

    def _set_header_font_size(self) -> float:
        maximum_width = self._column_width * .8

        if self.style.header_divider_width and self.style.header_divider_color:
            maximum_width -= self.style.header_divider_width

        current_size = self._column_width  # Set an upper bound to keep the column header at most squarish

        for header in self.grid.headers:
            possible_size = get_font_size_maximum_width(header, maximum_width, self.style.header_font_name)
            if possible_size < current_size:
                current_size = possible_size

        self._header_font_size = current_size
        self._header_height = self.layout.header_pad * self._header_font_size

    def _set_date_font_size(self) -> float:
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

        letter_widths = (stringWidth(letter, self.style.letter_font_name, self._default_letter_font_size)
                         for letter in all_letters)
        max_letter_width = max(*letter_widths)

        # Allow up to the lesser of half the cell, or 60% of the remaining space
        space_available = min((self._column_width - max_letter_width)*.6, self._column_width / 2)
        max_day_widths = (get_font_size_maximum_width(day, space_available, self.style.date_font_name)
                          for day in all_dates if day)

        theoretical_max = min(*max_day_widths)

        # Allow either the width-based max from above, or half the cell height
        self._date_font_size = min(theoretical_max, (self.layout.inner_height / len(self.grid.grid)) * .5)

    def _set_default_letter_font_size(self) -> float:
        all_letters = set()

        for row in self.grid.grid:
            for col in row:
                if col and col.letter:
                    all_letters.add(col.letter)

        # Letters get 80% of the cell
        maximum_width = self._column_width * .8

        if self.style.grid_line_color and self.style.grid_line_width:
            maximum_width -= self.style.grid_line_width

        # Maximum of 80% of the row height, if we have a really weirdly shaped calendar here
        current_size = self._row_height
        for letter in all_letters:
            possible_size = get_font_size_maximum_width(letter, maximum_width, self.style.date_font_name)

            if possible_size < current_size:
                current_size = possible_size

        self._default_letter_font_size = current_size

    def _set_y_pos_below_header(self):
        """Get the Y position that will be right below the title"""

        outline_width = 0
        if self.style.outline_width and self.style.outline_color:
            outline_width = self.style.outline_width

        self._y_pos_below_header = (self.layout.y_pos + self.layout.bottom_margin + self.layout.inner_height -
                                    self._title_font_size - self._header_height - outline_width)

    def _set_row_height(self):
        grid_height = self._y_pos_below_header - self.layout.y_pos - self.layout.bottom_margin

        self._row_height = grid_height / max(len(self.grid.grid), self.minimum_row_count_calculation)

    def _calculate_internals(self):
        """Calculate all the internal values"""

        self._set_title_font_size()
        self._set_header_font_size()
        self._set_y_pos_below_header()
        self._set_row_height()
        self._set_default_letter_font_size()
        self._set_date_font_size()


def get_font_size_maximum_width(text: str, maximum: float, font: str) -> float:
    """Get the maximum font size to fit some given text into a given width"""

    font_size = 12
    width = stringWidth(text, font, font_size)
    return maximum/width * font_size
