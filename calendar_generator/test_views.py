"""Tests for calendar views"""

import pytest
from datetime import date

from accounts.models import User

from django.test.client import Client
from django.urls import reverse
from django.template.response import TemplateResponse

from . import models


@pytest.mark.django_db
def test_calendar_index(client: Client, static_files):
    """Test that the landing page of a calendar works"""

    calendar = models.Calendar()
    calendar.title = "Test calendar"
    calendar.start_date = date(2024, 9, 1)
    calendar.end_date = date(2025, 6, 30)
    calendar.save()

    models.Day.objects.create(calendar=calendar, letter="A", position=0)
    models.Day.objects.create(calendar=calendar, letter="B", position=1)
    models.Day.objects.create(calendar=calendar, letter="C", position=2)

    user = User()
    user.email = "example@example.org"
    user.is_superuser = True
    user.save()

    client.force_login(user)
    url = reverse("calendar_generator:calendar", kwargs={"pk": calendar.pk})
    resp = client.get(url)
    assert isinstance(resp, TemplateResponse)
    assert resp.template_name == ["calendar_generator/calendar.html"]


@pytest.mark.django_db
def test_custom_calendar_landing_render(client: Client, superuser: User, static_files):
    """Test that the page to select the options for a custom calendar works"""

    calendar = models.Calendar()
    calendar.title = "Test calendar"
    calendar.start_date = date(2024, 9, 1)
    calendar.end_date = date(2025, 6, 30)
    calendar.save()

    models.Day.objects.create(calendar=calendar, letter="A", position=0)
    models.Day.objects.create(calendar=calendar, letter="B", position=1)
    models.Day.objects.create(calendar=calendar, letter="C", position=2)

    client.force_login(superuser)
    url = reverse("calendar_generator:custom", kwargs={"calendar_id": calendar.pk})
    resp = client.get(url)
    assert isinstance(resp, TemplateResponse)
    assert resp.template_name == "calendar_generator/custom.html"
