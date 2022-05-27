"""Models for calendar utility"""

import datetime

from typing import Dict, Set, List, Iterable, Optional

from django.db import models
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from django.core.validators import MaxValueValidator, MinValueValidator

from reportlab.lib import colors

from . import pdf


class Calendar(models.Model):
    """A calendar is a single calendar, such as 2021-2022"""

    title = models.CharField(max_length=254)

    start_date = models.DateField()
    end_date = models.DateField()

    sunday = models.BooleanField(default=False)
    monday = models.BooleanField(default=True)
    tuesday = models.BooleanField(default=True)
    wednesday = models.BooleanField(default=True)
    thursday = models.BooleanField(default=True)
    friday = models.BooleanField(default=True)
    saturday = models.BooleanField(default=False)

    class Meta:
        ordering = ['-start_date']

    def clean(self):
        if self.start_date > self.end_date:
            raise ValidationError("End date must be after start date")

    def get_absolute_url(self):
        """Absolute URL for Django admin"""

        return reverse_lazy('calendar_generator:calendar', kwargs={'pk': self.id})

    @property
    def day_flags(self) -> List[bool]:
        """
        A list of 7 booleans, one of each day of the week
        Monday is 0, to match the date.weekday() function for easy indexing
        """

        return [
            self.monday,
            self.tuesday,
            self.wednesday,
            self.thursday,
            self.friday,
            self.saturday,
            self.sunday,
        ]

    @property
    def day_numbers(self) -> List[int]:
        """All the days that are used, with Monday being 0, for calendar weekday generation"""

        # Transform True, True, True, True, True, False, False into 0, 1, 2, 3, 4
        return [i for i, day in enumerate(self.day_flags) if day]

    def get_date_letter_map(self) -> Dict[datetime.date, Optional[str]]:
        """
        A list of date to day mappings for this calendar,
        including every date that should be on the calendar,
        even skipped days
        """

        day_rotation = list(self.days.all())
        day_rotation.sort(key=lambda obj: obj.position)

        # Short circuit - if we aren't rotating, just shove None into everything
        # instead of having to have another loop
        if not day_rotation:
            return {d: None for d in self.get_all_days()}

        skip_days = self.get_all_skip_days()
        reset_days = self.get_all_reset_days()

        out: Dict[datetime.date, Optional[str]] = {}

        i = 0

        for date in self.get_all_days():
            if date in reset_days:
                # If we're resetting on this date, override the index to that day
                i = day_rotation.index(reset_days[date])

            day = day_rotation[i % len(day_rotation)]

            if date in skip_days:
                out[date] = None
                continue

            i += 1
            out[date] = day.letter

        return out

    def get_arbitrary_labels(self) -> Dict[datetime.date, str]:
        """Get all the arbitrary labels"""

        out = {}

        for obj in self.labels.all():
            assert isinstance(obj, ArbitraryLabel)

            out[obj.date] = obj.label

        return out

    def get_all_skip_days(self) -> Set[datetime.date]:
        """Return all the dates that should be skipped in the calendar"""

        out = set()
        for obj in self.skips.all():
            assert isinstance(obj, SkipDate)

            for date in obj.get_all_days():
                out.add(date)

        return out

    def get_all_reset_days(self) -> Dict[datetime.date, 'Day']:
        """Get all the reset days"""

        return {
            obj.date: obj.day for obj in self.reset_days.filter(day__calendar=self).select_related('day')
        }

    def get_all_days(self) -> Iterable[datetime.date]:
        """
        Get all days, skipped or not, falling on the enabled days
        between the start and end. This is what we should use to
        draw a calendar, should we be drawing a calendar
        """

        # This looks like true, true, true, true, true, false, false for Monday to Friday
        enabled_weekdays = self.day_flags

        start_date = self.start_date
        end_date = self.end_date

        assert isinstance(start_date, datetime.date)
        assert isinstance(end_date, datetime.date)

        total_days = (end_date - start_date).days + 1

        for offset in range(total_days):
            date = start_date + datetime.timedelta(days=offset)
            weekday = date.weekday()

            if not enabled_weekdays[weekday]:
                continue

            yield date

    def __str__(self):
        return self.title


class Day(models.Model):
    """A day is the kind of day - A, B, C - etc"""

    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE, related_name='days')
    letter = models.CharField(max_length=1)

    position = models.PositiveIntegerField(default=0, blank=True, null=True)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return self.letter


class SkipDate(models.Model):
    """Define a day or range of days to skip, such as for holidays"""

    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE, related_name='skips')
    date = models.DateField()
    end_date = models.DateField(blank=True, null=True)

    def get_all_days(self) -> Iterable[datetime.date]:
        """Return all the dates that should be skipped between the start and end dates"""

        assert isinstance(self.date, datetime.date)

        total_days = 1

        if self.end_date:
            assert isinstance(self.date, datetime.date)

            # We are inclusive of the end date, so add one
            total_days = (self.end_date - self.date).days + 1

        for offset in range(total_days):
            yield self.date + datetime.timedelta(days=offset)

    class Meta:
        unique_together = (('calendar', 'date'), )
        ordering = ['date']

    def clean(self):
        if self.end_date and self.date >= self.end_date:
            raise ValidationError("End date must be after start date")

    def __str__(self):
        return self.date.strftime("%Y-%m-%d")


class ResetDay(models.Model):
    """Reset the calendar to a specific day"""

    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE, related_name='reset_days')
    day = models.ForeignKey(Day, on_delete=models.DO_NOTHING)
    date = models.DateField()

    class Meta:
        unique_together = (
            ('calendar', 'date'),
        )

        ordering = ['date']

    def clean(self):
        assert isinstance(self.day, Day)
        assert isinstance(self.calendar, Calendar)

        if self.date not in self.calendar.get_date_letter_map():
            raise ValidationError("Reset date was not within calendar")

        if self.day.calendar != self.calendar:
            raise ValidationError("Reset day must be in a linked calendar")


class ArbitraryLabel(models.Model):
    """An arbitrary label on the calendar"""

    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE, related_name='labels')
    date = models.DateField()
    label = models.CharField(max_length=64)

    class Meta:
        unique_together = (
            ('calendar', 'date'),
        )

        ordering = ['date']

    def clean(self):
        assert isinstance(self.calendar, Calendar)

        if self.date not in self.calendar.get_date_letter_map():
            raise ValidationError("Label date was not within calendar")

    def __str__(self):
        return f"{self.date}/{self.label}"


class Layout(models.Model):
    """A layout that can be used in a calendar"""

    name = models.CharField(max_length=255)

    width = models.FloatField(validators=[MinValueValidator(0)], default=791)
    height = models.FloatField(validators=[MinValueValidator(0)], default=612)
    margins = models.FloatField(validators=[MinValueValidator(0)], default=36)
    line_width = models.FloatField(validators=[MinValueValidator(0)], default=1)

    header_font_name = models.CharField(max_length=255, default="HelveticaNeue-Bold")
    letter_font_name = models.CharField(max_length=255, default="HelveticaNeue-Light")
    date_font_name = models.CharField(max_length=255, default="HelveticaNeue-Light")
    title_font_name = models.CharField(max_length=255, default="HelveticaNeue-Bold")

    def to_pdf_layout(self) -> pdf.Layout:
        """Get the PDF layout"""

        return pdf.Layout(
            width=self.width,
            height=self.height,
            margins=self.margins,
            line_width=self.line_width,

            header_font_name=self.header_font_name,
            letter_font_name=self.letter_font_name,
            date_font_name=self.date_font_name,
            title_font_name=self.title_font_name,
        )

    def __str__(self):
        return self.name


class RGBColor(models.Model):
    """An RGB color"""

    name = models.CharField(max_length=255, unique=True)

    red = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1)])
    green = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1)])
    blue = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1)])
    alpha = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1)])

    class Meta:
        ordering = ['name']
        verbose_name = 'color'
        verbose_name_plural = 'colors'

    @property
    def reportlab_color(self) -> colors.Color:
        """Get the Reportlab color object"""

        return colors.Color(self.red, self.green, self.blue, self.alpha)

    def __str__(self):
        return self.name


class ColorSet(models.Model):
    """A color set that can be used on calendars"""

    name = models.CharField(max_length=255, unique=True)

    title_color = models.ForeignKey(RGBColor, related_name='+',
                                    on_delete=models.DO_NOTHING,
                                    help_text=('The color used to the title of the '
                                               'calendar, such as "January 2021"'))

    line_color = models.ForeignKey(RGBColor, related_name='+',
                                   on_delete=models.DO_NOTHING,
                                   help_text=('The color to use for all lines'))

    inner_grid_color = models.ForeignKey(RGBColor, related_name='+',
                                         on_delete=models.DO_NOTHING,
                                         help_text=('The color of the inner grid'))

    header_text_color = models.ForeignKey(RGBColor, related_name='+',
                                          on_delete=models.DO_NOTHING,
                                          help_text=("The color to use to draw the "
                                                     "headers: Monday, Tuesday, etc"))

    date_color = models.ForeignKey(RGBColor, related_name='+',
                                   on_delete=models.DO_NOTHING,
                                   help_text=("The color used to draw the day of the "
                                              "month, such as 1, 2, 3 ... 31"))

    letter_color = models.ForeignKey(RGBColor, related_name='+',
                                     on_delete=models.DO_NOTHING,
                                     help_text=('The color to use to "day of the week" '
                                                'letters, such as A, B, and C'))

    label_color = models.ForeignKey(RGBColor, related_name='+',
                                    on_delete=models.DO_NOTHING,
                                    help_text=('The color used to draw arbitrary '
                                               'labels such as "No school"'))

    divide_header = models.BooleanField(help_text=('If the header should be divided '
                                                   'using the inner grid color'))

    def to_style(self) -> pdf.ColorSet:
        """Get the PDF style for a color set"""

        return pdf.ColorSet(
            title_color=self.title_color.reportlab_color,
            line_color=self.line_color.reportlab_color,
            inner_grid_color=self.inner_grid_color.reportlab_color,
            header_text_color=self.header_text_color.reportlab_color,
            date_color=self.date_color.reportlab_color,
            letter_color=self.letter_color.reportlab_color,
            label_color=self.label_color.reportlab_color,
            divide_header=self.divide_header
        )

    def __str__(self):
        return self.name


class MonthlyDisplaySet(models.Model):
    """A "favorite" view for a monthly calendar"""

    name = models.CharField(max_length=255, unique=True)
    layout = models.ForeignKey(Layout, on_delete=models.CASCADE, related_name='+')
    color_set = models.ForeignKey(ColorSet, on_delete=models.CASCADE, related_name='+')

    def __str__(self):
        return self.name


class OnePageDisplaySet(models.Model):
    """A "favorite" view for a one page calendar"""

    name = models.CharField(max_length=255, unique=True)
    layout = models.ForeignKey(Layout, on_delete=models.CASCADE, related_name='+')
    color_set = models.ForeignKey(ColorSet, on_delete=models.CASCADE, related_name='+')

    def __str__(self):
        return self.name


def _to_optional_color(color: Optional[RGBColor]) -> Optional[colors.Color]:
    if color:
        return color.reportlab_color

    return None
