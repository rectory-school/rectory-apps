"""Tests for sync utilities"""

from base64 import encode
import pytest

from blackbaud.sync import encode_token

secret_encode_tests = [("asdf", "1234", "YXNkZjoxMjM0")]


@pytest.mark.parametrize("key,secret,expected", secret_encode_tests)
def test_secret_encode(key: str, secret: str, expected: str):
    actual = encode_token(key, secret)
    assert actual == expected
