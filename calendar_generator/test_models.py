"""Tests for the calendar models"""

from datetime import date

import pytest

from . import models


def test_skip_date_range():
    obj = models.SkipDate(date=date(2021, 1, 5), end_date=date(2021, 1, 10))

    skips = list(obj.get_all_days())

    assert skips == [
        date(2021, 1, 5),
        date(2021, 1, 6),
        date(2021, 1, 7),
        date(2021, 1, 8),
        date(2021, 1, 9),
        date(2021, 1, 10), ]


def test_skip_date():
    obj = models.SkipDate(date=date(2021, 1, 5))

    skips = list(obj.get_all_days())

    assert skips == [date(2021, 1, 5), ]


@pytest.mark.django_db
def test_skip_multiple_dates():
    c = models.Calendar()
    c.title = "Test"
    c.start_date = date(2021, 1, 1)
    c.end_date = date(2021, 12, 31)

    c.save()

    models.SkipDate.objects.create(calendar=c, date=date(2021, 1, 5))
    models.SkipDate.objects.create(calendar=c, date=date(2021, 2, 1), end_date=date(2021, 2, 5))

    expected_days = {
        date(2021, 1, 5),
        date(2021, 2, 1),
        date(2021, 2, 2),
        date(2021, 2, 3),
        date(2021, 2, 4),
        date(2021, 2, 5), }

    assert c.get_all_skip_days() == expected_days


@pytest.mark.django_db
def test_day_generation():
    c = models.Calendar()
    c.title = "Test"
    c.start_date = date(2021, 1, 4)
    c.end_date = date(2021, 1, 15)

    c.save()

    models.SkipDate.objects.create(calendar=c, date=date(2021, 1, 6))
    models.Day.objects.create(calendar=c, letter="A", position=0)
    models.Day.objects.create(calendar=c, letter="B", position=1)

    expected = {
        date(2021, 1, 4): "A",
        date(2021, 1, 5): "B",
        # 6 is a skip
        date(2021, 1, 7): "A",
        date(2021, 1, 8): "B",
        date(2021, 1, 11): "A",
        date(2021, 1, 12): "B",
        date(2021, 1, 13): "A",
        date(2021, 1, 14): "B",
        date(2021, 1, 15): "A",
    }

    actual = c.get_date_letter_map()

    assert actual == expected


@pytest.mark.django_db
def test_calendar_get_all_relevant_days():
    c = models.Calendar()
    c.title = "Test"
    c.start_date = date(2021, 1, 4)
    c.end_date = date(2021, 1, 15)

    c.save()

    models.SkipDate.objects.create(calendar=c, date=date(2021, 1, 6))

    expected = [
        date(2021, 1, 4),
        date(2021, 1, 5),
        # 6 is a skip
        date(2021, 1, 7),
        date(2021, 1, 8),
        date(2021, 1, 11),
        date(2021, 1, 12),
        date(2021, 1, 13),
        date(2021, 1, 14),
        date(2021, 1, 15),
    ]

    actual = list(c.get_all_dates())

    assert actual == expected
