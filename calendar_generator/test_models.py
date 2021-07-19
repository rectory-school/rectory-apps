"""Tests for the calendar models"""

from datetime import date

import pytest

from . import models


def test_skip_date_range():
    """Test a range of skip dates"""

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
    """Test single date skipping"""

    obj = models.SkipDate(date=date(2021, 1, 5))

    skips = list(obj.get_all_days())

    assert skips == [date(2021, 1, 5), ]


@pytest.mark.django_db
def test_skip_multiple_dates():
    """Test multiple skip date entries, with a skip date range"""

    cal = models.Calendar()
    cal.title = "Test"
    cal.start_date = date(2021, 1, 1)
    cal.end_date = date(2021, 12, 31)

    cal.save()

    models.SkipDate.objects.create(calendar=cal, date=date(2021, 1, 5))
    models.SkipDate.objects.create(calendar=cal, date=date(2021, 2, 1), end_date=date(2021, 2, 5))

    expected_days = {
        date(2021, 1, 5),
        date(2021, 2, 1),
        date(2021, 2, 2),
        date(2021, 2, 3),
        date(2021, 2, 4),
        date(2021, 2, 5), }

    assert cal.get_all_skip_days() == expected_days


@pytest.mark.django_db
def test_day_generation():
    """Test that day generation with skips is accurate"""

    cal = models.Calendar()
    cal.title = "Test"
    cal.start_date = date(2021, 1, 4)
    cal.end_date = date(2021, 1, 15)
    cal.monday = True
    cal.tuesday = True
    cal.wednesday = True
    cal.thursday = True
    cal.friday = True
    cal.saturday = False
    cal.sunday = False

    cal.save()

    models.SkipDate.objects.create(calendar=cal, date=date(2021, 1, 6))
    models.Day.objects.create(calendar=cal, letter="A", position=0)
    models.Day.objects.create(calendar=cal, letter="B", position=1)

    expected = {
        date(2021, 1, 4): "A",
        date(2021, 1, 5): "B",
        date(2021, 1, 6): None,
        date(2021, 1, 7): "A",
        date(2021, 1, 8): "B",
        date(2021, 1, 11): "A",
        date(2021, 1, 12): "B",
        date(2021, 1, 13): "A",
        date(2021, 1, 14): "B",
        date(2021, 1, 15): "A",
    }

    actual = cal.get_date_letter_map()

    assert actual == expected


@pytest.mark.django_db
def test_day_generation_empty():
    """Test that empty day generation is as expected"""

    cal = models.Calendar()
    cal.title = "Test"
    cal.start_date = date(2021, 1, 4)
    cal.end_date = date(2021, 1, 15)
    cal.monday = True
    cal.tuesday = True
    cal.wednesday = True
    cal.thursday = True
    cal.friday = True
    cal.saturday = False
    cal.sunday = False

    cal.save()

    expected = {
        date(2021, 1, 4): None,
        date(2021, 1, 5): None,
        date(2021, 1, 6): None,
        date(2021, 1, 7): None,
        date(2021, 1, 8): None,
        date(2021, 1, 11): None,
        date(2021, 1, 12): None,
        date(2021, 1, 13): None,
        date(2021, 1, 14): None,
        date(2021, 1, 15): None,
    }

    actual = cal.get_date_letter_map()

    assert actual == expected
