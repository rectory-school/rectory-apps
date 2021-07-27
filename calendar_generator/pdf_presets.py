"""PDF presets"""

from dataclasses import dataclass

from reportlab.lib import colors
from reportlab.lib.units import inch

from . import pdf

rectory_orange = colors.Color(219/255.0, 119/255.0, 52/255.0)

black_and_white = pdf.CalendarStyle(
    outline_color=colors.black,
    grid_line_color=colors.black,
    title_color=colors.black,
    label_color=colors.darkgray,

    header_background_color=colors.black,

    header_text_color=colors.white,
    letter_color=colors.black,
    date_color=colors.black,
)

rectory_colors = pdf.CalendarStyle(
    outline_color=rectory_orange,
    grid_line_color=rectory_orange,
    title_color=rectory_orange,
    label_color=colors.darkgray,

    header_background_color=rectory_orange,
    header_divider_color=colors.white,

    header_text_color=colors.white,
    letter_color=colors.black,
    date_color=rectory_orange,
)

blues = pdf.CalendarStyle(
    outline_color=colors.darkblue,
    grid_line_color=colors.darkblue,
    title_color=colors.darkblue,
    label_color=colors.darkgray,

    header_background_color=colors.darkblue,
    header_divider_color=colors.white,

    header_text_color=colors.white,
    letter_color=colors.black,
    date_color=colors.mediumblue,
)

AVAILABLE_COLOR_PRESETS = (
    ("Black & White", black_and_white),
    ("Rectory Colors", rectory_colors),
    ("Blue", blues),
)


@dataclass
class PDFSizePreset:
    """Preset for a PDF size"""

    width: float
    height: float
    top_margin: float
    bottom_margin: float
    left_margin: float
    right_margin: float

    @property
    def inner_height(self) -> float:
        """Calculate the inner height of the PDF"""

        return self.height - self.top_margin - self.bottom_margin

    @property
    def inner_width(self) -> float:
        """Calculate the inner width of the PDF"""

        return self.width - self.left_margin - self.right_margin


letter_print = PDFSizePreset(width=11*inch, height=8.5*inch,
                             top_margin=.5*inch, bottom_margin=.5*inch,
                             left_margin=.5*inch, right_margin=.5*inch)

AVAILABLE_SIZE_PRESETS = (
    ("Letter Landscape: Print", letter_print),
    ("Letter Landscape: Embedded", letter_print),
)
