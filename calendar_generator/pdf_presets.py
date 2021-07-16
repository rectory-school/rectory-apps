"""PDF presets"""

from reportlab.lib import colors

from . import pdf

color_accent = colors.indigo

black_and_white = pdf.CalendarStyle(
    outline_color=colors.black,
    grid_line_color=colors.black,
    title_color=colors.black,

    header_background_color=colors.black,

    header_text_color=colors.white,
    letter_color=colors.black,
    date_color=colors.black,
)

color = pdf.CalendarStyle(
    outline_color=colors.black,
    grid_line_color=colors.black,
    title_color=color_accent,

    header_background_color=color_accent,
    header_divider_color=colors.white,

    header_text_color=colors.white,
    letter_color=colors.black,
    date_color=colors.black,
)

PRESET_MAP = {
    'black': black_and_white,
    'color': color,
}