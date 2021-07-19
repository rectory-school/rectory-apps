"""PDF presets"""

from reportlab.lib import colors

from . import pdf

rectory_orange = colors.Color(219/255.0, 119/255.0, 52/255.0)

black_and_white = pdf.CalendarStyle(
    outline_color=colors.black,
    grid_line_color=colors.black,
    title_color=colors.black,

    header_background_color=colors.black,

    header_text_color=colors.white,
    letter_color=colors.black,
    date_color=colors.black,
)

rectory_colors = pdf.CalendarStyle(
    outline_color=rectory_orange,
    grid_line_color=rectory_orange,
    title_color=rectory_orange,

    header_background_color=rectory_orange,
    header_divider_color=colors.white,

    header_text_color=colors.white,
    letter_color=colors.black,
    date_color=rectory_orange,
)

rectory_colors = pdf.CalendarStyle(
    outline_color=rectory_orange,
    grid_line_color=rectory_orange,
    title_color=rectory_orange,

    header_background_color=rectory_orange,
    header_divider_color=colors.white,

    header_text_color=colors.white,
    letter_color=colors.black,
    date_color=rectory_orange,
)

blues = pdf.CalendarStyle(
    outline_color=colors.ReportLabBlue,
    grid_line_color=colors.ReportLabBlue,
    title_color=colors.ReportLabBlue,

    header_background_color=colors.ReportLabBlue,
    header_divider_color=colors.white,

    header_text_color=colors.white,
    letter_color=colors.black,
    date_color=colors.darkgray,
)

AVAILABLE_COLOR_PRESETS = (
    ("Black & White", black_and_white),
    ("Rectory Colors", rectory_colors),
    ("Blue", blues),
)
