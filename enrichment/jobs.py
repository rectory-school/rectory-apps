"""Scheduled jobs for enrichment"""

from django.db import transaction
from django.utils import timezone

from job_runner.registration import register_job
from job_runner.environment import RunEnv

import structlog

from .models import EmailConfig
from .emails import execute_job

log = structlog.get_logger()


@register_job(300)
def tick_emails(env: RunEnv):
    log.debug("Beginning email tick")
    now = timezone.now()

    with transaction.atomic():
        for job in EmailConfig.objects.select_for_update().filter(enabled=True):
            if env.is_stopping:
                return

            next_run = job.next_run
            if not next_run:
                continue

            if next_run <= now:
                log.info("Preparing enrichment outgoing emails", job=job)

                with transaction.atomic():
                    try:
                        execute_job(job, next_run.date())
                        log.info("Finished creating outgoing emails", job=job)
                    except Exception as exc:
                        log.exception("Error when running job", exc=exc)
