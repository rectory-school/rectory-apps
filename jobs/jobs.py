"""Test jobs for jobs library"""

import logging
from jobs import schedule

log = logging.getLogger(__name__)


@schedule(0, 30)
def hello():
    """Say hello"""

    log.debug("Saying hello")


@schedule(5, 60)
def hello_2():
    """Say hello"""

    log.debug("Saying hello again")
