"""Periodic jobs for sending email"""

import logging
from random import choice, randint

from django.utils import timezone
from django.db import transaction
from jobs import schedule

from . import models

log = logging.getLogger(__name__)


@schedule(60)
def send_emails() -> bool:
    """Send all emails that have been scheduled"""

    unsent_pks = models.OutgoingMessage.objects.filter(sent_at__isnull=True).values('pk')
    if not unsent_pks:
        log.info("No more unsent PKs")
        return False

    pk_to_send = choice(unsent_pks)['pk']
    # We are going to send one email at a time in order to guarantee we
    # don't mess up any transactions too badly and can just let exceptions
    # propagate up

    with transaction.atomic():
        to_send = models.OutgoingMessage.objects.select_for_update(skip_locked=True).get(pk=pk_to_send)
        assert isinstance(to_send, models.OutgoingMessage)

        if not to_send:
            log.info("Hit a race, %d is not available", pk_to_send)
            return True

        if to_send.sent_at:
            log.info("Hit a race, %d was already sent", pk_to_send)
            return True

        msg = to_send.get_django_email()
        msg.send()
        to_send.sent_at = timezone.now()
        to_send.save()

        # We should run again
        return True
