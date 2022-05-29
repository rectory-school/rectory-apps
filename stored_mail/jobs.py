"""Periodic jobs for sending email"""

import logging

from datetime import timedelta

from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from job_runner.registration import register_job
from job_runner.environment import RunEnv
from . import models

log = logging.getLogger(__name__)


@register_job(15)
def send_emails(env: RunEnv):
    """Send all emails that have been scheduled"""

    with transaction.atomic():
        # Wait at least an hour between attempts
        last_attempt_query = (Q(last_send_attempt__isnull=True) |
                              Q(last_send_attempt__lte=(timezone.now() - timedelta(hours=1))))

        # Don't send emails that were created more than 7 days ago
        # TODO: Make the 7 day threshold configurable
        created_at_query = Q(created_at__gte=timezone.now() - timedelta(days=7))

        sent_at_query = Q(sent_at__isnull=True)

        candidate_query = last_attempt_query & created_at_query & sent_at_query

        to_send = models.OutgoingMessage.objects.filter(candidate_query).select_for_update(skip_locked=True).first()

        if not to_send:
            log.info("No messages to send")
            # Once we don't have an email to send, return without
            # requesting an immediate rerun
            return

        assert isinstance(to_send, models.OutgoingMessage)

        try:
            msg = to_send.get_django_email()
            msg.send()
            to_send.sent_at = timezone.now()
            to_send.last_send_attempt = None

        # I always want to be able to store the last send attempt,
        # and if I throw an exception inside the transaction I can't do that.
        except Exception as exc:  # pylint: disable=broad-except
            log.exception("Unable to send email %d: %s", to_send.pk, exc)
            to_send.last_send_attempt = timezone.now()

        to_send.save()

    # Keep running the job until we don't have any emails to send
    env.request_rerun()
