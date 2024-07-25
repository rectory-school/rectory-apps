import pytest

import uuid

import tempfile
import shutil
from contextlib import contextmanager
from django.core.management import call_command
from django.test import override_settings

from accounts.models import User


@contextmanager
def static_files_context():
    static_root = tempfile.mkdtemp(prefix="test_static")
    with override_settings(STATIC_ROOT=static_root):
        try:
            call_command("collectstatic", "--noinput")
            yield
        finally:
            shutil.rmtree(static_root)


@pytest.fixture()
def superuser() -> User:
    user = User()
    user.email = f"{uuid.uuid4().hex}@example.org"
    user.is_superuser = True
    user.save()

    return user


@pytest.fixture()
def static_files():
    with static_files_context():
        yield
