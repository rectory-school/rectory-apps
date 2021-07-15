"""This is a baseline test for pytest"""


def add(a: int, b: int) -> int:
    return a + b


def test_add():
    assert add(7, 13) == 20
