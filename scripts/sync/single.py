"""Helpers to run methods only once"""

from functools import wraps

_already_run = set()


def run_once(f):
    """Runs a function (successfully) only once.

    The running can be reset by setting the `has_run` attribute to False
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        key = (f, *args)

        if key not in _already_run:
            _already_run.add(key)
            return f(*args, **kwargs)

    return wrapper
