"""Test jobs for jobs library"""

import logging
from jobs import schedule

log = logging.getLogger(__name__)


@schedule(5)
def hello():
    """Say hello"""

    log.debug("Saying hello")
