"""Parsers for managers"""

import logging

log = logging.getLogger(__name__)


def active_parse(val: str) -> bool:
    if val == "":
        return False

    if val == "0":
        return True

    if val == "1":
        return True

    log.warning("Unknown value '%s' when parsing acive field, assuming false", val)
    return False
