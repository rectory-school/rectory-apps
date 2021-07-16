"""Models for calendar utility"""

import datetime

from typing import Dict, Set, List, Iterable

from django.db import models
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy


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

    def clean(self):
        if self.start_date > self.end_date:
            raise ValidationError("End date must be after start date")

    def get_absolute_url(self):
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

    def get_date_letter_map(self) -> Dict[datetime.date, str]:
        """ A list of date to day mappings for this calendar"""

        day_rotation = list(self.days.all())
        day_rotation.sort(key=lambda obj: obj.position)

        out = {}

        for i, date in enumerate(self.get_all_dates()):
            day = day_rotation[i % len(day_rotation)]
            assert isinstance(day, Day)

            out[date] = day.letter

        return out

    def get_all_skip_days(self) -> Set[datetime.date]:
        """Return all the dates that should be skipped in the calendar"""

        out = set()
        for obj in self.skips.all():
            assert isinstance(obj, SkipDate)

            for date in obj.get_all_days():
                out.add(date)

        return out

    def get_all_dates(self):
        """Get all non-skipped dates that are in scope"""

        skip_dates = self.get_all_skip_days()

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

            if date in skip_dates:
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

        out = set()

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
        return self.start_date.strftime("%Y-%m-%d")

# Reset date was never used and was removed