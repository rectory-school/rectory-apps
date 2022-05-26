
from django.db import migrations

inch = 72.0
cm = inch / 2.54
mm = cm * 0.1
pica = 12.0


_colors = {
    'Black': 0,
    'White': 255,
    'Dark Gray': 0xA9,
    'Rectory Orange': (219, 119, 52),
    'Dark Blue': (0, 0, 0x8B),
    'Medium Blue': (0x66, 0xCD,  0xAA)
}

_color_sets = {
    'Black and White': {
        'outline_color': 'Black',
        'grid_line_color': 'Black',
        'title_color': 'Black',
        'label_color': 'Dark Gray',
        'header_background_color': 'Black',
        'header_text_color': 'White',
        'letter_color': 'Black',
        'date_color': 'Black'
    },
    'Rectory Colors': {
        'outline_color': 'Rectory Orange',
        'grid_line_color': 'Rectory Orange',
        'title_color': 'Rectory Orange',
        'label_color': 'Dark Gray',
        'header_background_color': 'Rectory Orange',
        'header_divider_color': 'White',
        'header_text_color': 'White',
        'letter_color': 'Black',
        'date_color': 'Rectory Orange'
    },
    'Blue': {
        'outline_color': 'Dark Blue',
        'grid_line_color': 'Dark Blue',
        'title_color': 'Dark Blue',
        'label_color': 'Dark Gray',
        'header_background_color': 'Dark Blue',
        'header_divider_color': 'White',
        'header_text_color': 'White',
        'letter_color': 'Black',
        'date_color': 'Medium Blue'
    }
}


def _quick_layout(width: float, height: float, margins: float):
    return {
        'width': width,
        'height': height,
        'top_margin': margins,
        'bottom_margin': margins,
        'left_margin': margins,
        'right_margin': margins,
        'header_divider_width': 1,
        'outline_width': 1,
        'grid_line_width': 1,

    }


_layouts = {
    'Letter Landscape (Print)': _quick_layout(11 * inch, 8.5 * inch, .5 * inch),
    'Letter Landscape (Embedded)': _quick_layout(11 * inch, 8.5 * inch, 0),
    'Letter Portrait (Print)': _quick_layout(8.5 * inch, 11 * inch, .5 * inch),
    'Letter Portrait (Embedded)': _quick_layout(8.5 * inch, 11 * inch, 0),

    'A4 Landscape (Print)': _quick_layout(297*mm, 210 * mm, 17*mm),
    'A4 Landscape (Embedded)': _quick_layout(297*mm, 210 * mm, 0),
    'A4 Portrait (Print)': _quick_layout(210*mm, 297 * mm, 17*mm),
    'A4 Portrait (Embedded)': _quick_layout(210*mm, 297 * mm, 0),
}


def _get_color(val):
    if isinstance(val, int) or isinstance(val, float):
        return _get_color((val, val, val))

    red, green, blue = val

    red_scaled = red/255.0
    green_scaled = green/255.0
    blue_scaled = blue/255.0

    return (red_scaled, green_scaled, blue_scaled)


def make_colors(apps, schema_editor):
    """Create the default colors"""

    del schema_editor

    RGBColor = apps.get_model('calendar_generator', 'RGBColor')

    for name, val in _colors.items():
        red, green, blue = _get_color(val)

        RGBColor.objects.create(name=name, red=red, green=green, blue=blue, alpha=1)


def delete_colors(apps, schema_editor):
    """Delete the default colors"""

    del schema_editor

    RGBColor = apps.get_model('calendar_generator', 'RGBColor')
    for name in _colors:
        RGBColor.objects.get(name=name).delete()


def make_color_sets(apps, schema_editor):
    """Create the default color sets"""

    del schema_editor

    RGBColor = apps.get_model('calendar_generator', 'RGBColor')
    ColorSet = apps.get_model('calendar_generator', 'ColorSet')

    colors_by_name = {obj.name: obj for obj in RGBColor.objects.all()}

    for name, vals in _color_sets.items():
        params = {'name': name}

        for key, val in vals.items():
            params[key] = colors_by_name[val]

        ColorSet.objects.create(**params)


def delete_color_sets(apps, schema_editor):
    """Delete the default color sets"""

    del schema_editor

    ColorSet = apps.get_model('calendar_generator', 'ColorSet')

    for name in _color_sets:
        ColorSet.objects.get(name=name).delete()


def make_layouts(apps, schema_editor):
    """Make the default layouts"""

    del schema_editor
    Layout = apps.get_model('calendar_generator', 'Layout')

    for name, vals in _layouts.items():
        params = {k: v for k, v in vals.items()}
        params['name'] = name

        Layout.objects.create(**params)


def delete_layouts(apps, schema_editor):
    """Delete the default layouts"""

    del schema_editor
    Layout = apps.get_model('calendar_generator', 'Layout')

    for name in _layouts:
        Layout.objects.get(name=name).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('calendar_generator', '0009_colorset_layout_rgbcolor'),
    ]

    operations = [
        migrations.RunPython(make_colors, delete_colors),
        migrations.RunPython(make_color_sets, delete_color_sets),
        migrations.RunPython(make_layouts, delete_layouts)
    ]
