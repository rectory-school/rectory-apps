"""Teacher sync"""

import logging
from manager import SyncManager

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


class TeacherManager(SyncManager):
    apps_url_key = 'teachers'
    apps_key = 'teacher_id'
    ks_key = 'IDTEACHER'

    field_map = [
        ('teacher_id', 'IDTEACHER'),
        ('unique_name', 'NameUnique'),
        ('first_name', 'NameFirst'),
        ('last_name', 'NameLast'),
        ('prefix', 'NamePrefix'),
        ('email', 'EmailSchool'),
        ('active', 'Active Employee'),
    ]

    field_translations = {
        'active': active_parse,
    }
