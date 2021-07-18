"""Models for calendar utility"""

import datetime

from typing import Dict, Set, List, Iterable, Optional

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

        out = {}

        for i, date in enumerate(self.get_all_date_with_letters()):
            day = None
            if day_rotation:
                day = day_rotation[i % len(day_rotation)]

            if day:
                out[date] = day.letter
            else:
                out[date] = None

        return out

    def get_all_skip_days(self) -> Set[datetime.date]:
        """Return all the dates that should be skipped in the calendar"""

        out = set()
        for obj in self.skips.all():
            assert isinstance(obj, SkipDate)

            for date in obj.get_all_days():
                out.add(date)

        return out

    def get_all_date_with_letters(self) -> Iterable[datetime.date]:
        """Get all non-skipped dates that are in scope"""

        skip_dates = self.get_all_skip_days()

        for day in self.get_all_days():
            if day in skip_dates:
                continue

            yield day

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

# Reset date was never used and was removed
