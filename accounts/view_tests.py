import pytest

from datetime import timedelta

from django.test.client import Client
from django.urls import reverse
from django.http.response import HttpResponseRedirect
from django.core import mail
from django.utils import timezone
from django.contrib import auth
from . import models


@pytest.mark.django_db
def test_email_login_send_code(client: Client):
    """Test that the code is sent for an email login"""

    user = models.User()
    user.email = "user@example.org"
    user.save()

    cfg = models.LoginConfiguration.get_solo()
    cfg.enable_email_login = True
    cfg.save()

    url = reverse("accounts:login-email")
    form_data = {"email_address": user.email}
    resp = client.post(url, form_data)
    assert isinstance(resp, HttpResponseRedirect)

    code = models.TemporaryLoginCode.objects.filter(user=user).get().code
    assert code

    assert len(mail.outbox) == 1
    msg = mail.outbox[0]

    # Sanity check to ensure the generated code is somewhere in the outgoing email
    assert code in msg.body


@pytest.mark.django_db
def test_email_login_with_code(client: Client):
    """Ensure a user can log in with a code"""

    user = models.User()
    user.email = "user@example.org"
    user.save()

    cfg = models.LoginConfiguration.get_solo()
    cfg.enable_email_login = True
    cfg.save()

    code_obj = models.TemporaryLoginCode()
    code_obj.user = user
    code_obj.expiration = timezone.now() + timedelta(minutes=30)
    code_obj.save()

    url = reverse("accounts:login-email", kwargs={"code": code_obj.code})
    resp = client.get(url)
    assert isinstance(resp, HttpResponseRedirect)

    logged_in_user = auth.get_user(client)
    assert logged_in_user == user


@pytest.mark.django_db
def test_request_code_disabled(client: Client):
    """When email codes are disabled, ensure they can't be sent"""

    cfg = models.LoginConfiguration.get_solo()
    cfg.enable_email_login = False
    cfg.save()

    url = reverse("accounts:login-email")
    landing_url = reverse("accounts:login")

    resp = client.get(url)
    assert isinstance(resp, HttpResponseRedirect)
    assert resp.url == landing_url
