"""Periodic jobs for sending email"""

import logging
from typing import Optional

from datetime import timedelta

from structlog import get_logger
from structlog.stdlib import BoundLogger

from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from job_runner.registration import register_job
from job_runner.environment import RunEnv
from . import models

log: BoundLogger = get_logger(__name__)


@register_job(15)
def send_emails(env: RunEnv):
    """Send all emails that have been scheduled"""

    with transaction.atomic():
        # Wait at least an hour between attempts
        last_attempt_query = Q(last_send_attempt__isnull=True) | Q(
            last_send_attempt__lte=(timezone.now() - timedelta(hours=1))
        )

        not_discarded_query = Q(discard_after__gt=timezone.now())

        sent_at_query = Q(sent_at__isnull=True)

        candidate_query = last_attempt_query & not_discarded_query & sent_at_query

        to_send: Optional[models.OutgoingMessage] = (
            models.OutgoingMessage.objects.filter(candidate_query)
            .select_for_update(skip_locked=True)
            .first()
        )

        if not to_send:
            # Once we don't have an email to send, return without
            # requesting an immediate rerun
            return

        try:
            log.info("Sending message", message_id=to_send.pk)
            msg = to_send.get_django_email()
            msg.send()
            to_send.sent_at = timezone.now()
            to_send.last_send_attempt = None
            log.info("Message sent", message_id=to_send.pk)

        # I always want to be able to store the last send attempt,
        # and if I throw an exception inside the transaction I can't do that.
        except Exception as exc:  # pylint: disable=broad-except
            log.exception("Unable to send email %d: %s", to_send.pk, exc)
            to_send.last_send_attempt = timezone.now()

        to_send.save()

    # Keep running the job until we don't have any emails to send
    env.request_rerun()
