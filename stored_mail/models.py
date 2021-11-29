"""Models for stored mail sender"""

import email.utils

from django.db import models

FIELD_OPTIONS = (
    ('to', 'To'),
    ('cc', 'Cc'),
    ('bcc', 'Bcc'),
)

_field_option_length = max((len(o[0]) for o in FIELD_OPTIONS))


class OutgoingMessage(models.Model):
    """Outgoing email stored for sending"""

    from_name = models.CharField(max_length=255)
    from_address = models.EmailField()

    subject = models.CharField(max_length=4096, blank=True)
    text = models.TextField(blank=True)
    html = models.TextField(blank=True)
    amp_html = models.TextField(blank=True)

    sent_at = models.DateTimeField(null=True)


class SendAddress(models.Model):
    """Address to send an email to"""

    name = models.CharField(max_length=255)
    address = models.EmailField()
    message = models.ForeignKey(OutgoingMessage, on_delete=models.CASCADE)
    field = models.CharField(choices=FIELD_OPTIONS, max_length=_field_option_length)

    def __str__(self):
        if not self.name:
            return self.address

        return email.utils.formataddr((self.name, self.address))

    class Meta:
        unique_together = (
            ('address', 'message'),
        )
