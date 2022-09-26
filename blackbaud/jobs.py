"""Periodic Blackbaud jobs"""

from django.utils import timezone
from django.db import transaction

from structlog import get_logger
from structlog.stdlib import BoundLogger

from job_runner.registration import register_job
from job_runner.environment import RunEnv

from blackbaud.sync import auto_sync, SyncNotReady, SyncNotEnabled

log: BoundLogger = get_logger(__name__)


@register_job(15, variance=30)
def sync_sis(env: RunEnv):
    """Sync with Blackbaud"""

    try:
        auto_sync()
    except SyncNotEnabled:
        log.debug("Sync is not currently enabled")
        return
    except SyncNotReady as exc:
        log.debug("Sync not ready")
