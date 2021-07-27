"""PDF presets"""

from reportlab.lib import colors
from reportlab.lib.units import inch

from . import pdf

rectory_orange = colors.Color(219/255.0, 119/255.0, 52/255.0)

black_and_white = pdf.ColorStyle(
    outline_color=colors.black,
    grid_line_color=colors.black,
    title_color=colors.black,
    label_color=colors.darkgray,

    header_background_color=colors.black,

    header_text_color=colors.white,
    letter_color=colors.black,
    date_color=colors.black,
)

rectory_colors = pdf.ColorStyle(
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

blues = pdf.ColorStyle(
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


letter_print = pdf.SizeStyle(width=11*inch, height=8.5*inch,
                             top_margin=.5*inch, bottom_margin=.5*inch,
                             left_margin=.5*inch, right_margin=.5*inch)

letter_embedded = pdf.SizeStyle(width=11*inch, height=8.5*inch,
                                top_margin=0, bottom_margin=0,
                                left_margin=0, right_margin=0)


def _quick(width: float, height: float, margins: float) -> pdf.SizeStyle:
    """Generate a size preset with equal margins"""

    return pdf.SizeStyle(width=width, height=height,
                         top_margin=margins, bottom_margin=margins,
                         left_margin=margins, right_margin=margins)


AVAILABLE_SIZE_PRESETS = (
    ("Letter Landscape: Print", _quick(11*inch, 8.5*inch, .5*inch)),
    ("Letter Landscape: Embedded", _quick(11*inch, 8.5*inch, 0)),
)
