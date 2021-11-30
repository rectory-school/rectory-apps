"""Periodic jobs for sending email"""

import logging

from datetime import timedelta

from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from jobs import schedule

from . import models

log = logging.getLogger(__name__)


@schedule(15)
def send_emails() -> bool:
    """Send all emails that have been scheduled"""

    # TODO: I should probably re-introduce some batching here

    with transaction.atomic():
        # Wait at least an hour between attempts
        last_attempt_query = (Q(last_send_attempt__isnull=True) |
                              Q(last_send_attempt__lte=(timezone.now() - timedelta(hours=1))))

        # Don't send emails that were created more than 7 days ago
        # TODO: Make the 7 day threshold configurable
        created_at_query = Q(created_at__gte=timezone.now() - timedelta(days=7))

        sent_at_query = Q(sent_at__isnull=True)

        candidate_query = last_attempt_query & created_at_query & sent_at_query

        to_send = models.OutgoingMessage.objects.filter(candidate_query).first()
        assert isinstance(to_send, models.OutgoingMessage)

        if not to_send:
            log.info("No messages to send")
            return False

        try:
            msg = to_send.get_django_email()
            msg.send()
            to_send.sent_at = timezone.now()
            to_send.last_send_attempt = None

        except Exception as exc:  # pytlint disable=broad-except
            log.exception("Unable to send email %d: %s", to_send.pk, exc)
            to_send.last_send_attempt = timezone.now()

        to_send.save()

    return True
