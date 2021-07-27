"""PDF presets"""

from reportlab.lib import colors
from reportlab.lib.units import inch, mm

from . import pdf

rectory_orange = colors.Color(219/255.0, 119/255.0, 52/255.0)

black_and_white = pdf.FormatStyle(
    outline_color=colors.black,
    grid_line_color=colors.black,
    title_color=colors.black,
    label_color=colors.darkgray,

    header_background_color=colors.black,

    header_text_color=colors.white,
    letter_color=colors.black,
    date_color=colors.black,
)

rectory_colors = pdf.FormatStyle(
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

blues = pdf.FormatStyle(
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

AVAILABLE_STYLE_PRESETS = (
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


AVAILABLE_LAYOUT_PRESETS = (
    ("Letter Landscape (Print)", _quick(11*inch, 8.5*inch, .5*inch)),
    ("Letter Landscape (Embedded)", _quick(11*inch, 8.5*inch, 0)),
    ("Letter (Print)", _quick(8.5*inch, 11*inch, .5*inch)),
    ("Letter (Embedded)", _quick(8.5*inch, 11*inch, 0)),

    ("A4 Landscape (Print)", _quick(297*mm, 210*mm, 17*mm)),
    ("A4 Landscape (Embedded)", _quick(297*mm, 210*mm, 0*mm)),
    ("A4: (Print)", _quick(210*mm, 297*mm, 17*mm)),
    ("A4: (Embedded)", _quick(210*mm, 297*mm, 0*mm)),
)
