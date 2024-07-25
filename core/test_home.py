"""Tests to make sure we can render static URLs appropriately"""

from django.test import Client
from django.urls import reverse
from django.template.response import TemplateResponse

import tempfile
import shutil
from contextlib import contextmanager
from django.core.management import call_command
from django.test import override_settings


@contextmanager
def static_files_context():
    static_root = tempfile.mkdtemp(prefix="test_static")
    with override_settings(STATIC_ROOT=static_root):
        try:
            call_command("collectstatic", "--noinput")
            yield
        finally:
            shutil.rmtree(static_root)


def test_home_url():
    url = reverse("home")

    assert url == "/"


def test_home_render(client: Client):
    """This mainly checks for things like base CSS/JS,
    which has bitten me in the past"""

    url = reverse("home")
    with static_files_context():
        resp = client.get(url)
    assert isinstance(resp, TemplateResponse)
    assert resp.template_name == ["home.html"]
