"""Tests to make sure we can render static URLs appropriately"""

from django.test import Client
from django.urls import reverse
from django.template.response import TemplateResponse


def test_home_url():
    url = reverse("home")

    assert url == "/"


def test_home_render(client: Client, static_files):
    """This mainly checks for things like base CSS/JS,
    which has bitten me in the past"""

    url = reverse("home")
    resp = client.get(url)
    assert isinstance(resp, TemplateResponse)
    assert resp.template_name == ["home.html"]
