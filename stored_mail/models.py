"""Models for stored mail sender"""

import email.utils
import email.message
from email.headerregistry import Address
from typing import List
from uuid import uuid4

from django.db import models
from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives

FIELD_OPTIONS = (
    ('to', 'To'),
    ('cc', 'Cc'),
    ('bcc', 'Bcc'),
    ('reply-to', 'Reply To'),
)

_field_option_length = max((len(o[0]) for o in FIELD_OPTIONS))


class OutgoingMessage(models.Model):
    """Outgoing email stored for sending"""

    unique_id = models.UUIDField(default=uuid4, unique=True)

    from_name = models.CharField(max_length=255)
    from_address = models.EmailField()

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    subject = models.CharField(max_length=4096, blank=True)
    text = models.TextField()
    html = models.TextField(blank=True)

    sent_at = models.DateTimeField(null=True, db_index=True)
    last_send_attempt = models.DateTimeField(null=True, db_index=True)
    discard_after = models.DateTimeField()

    @property
    def message_id(self) -> str:
        """Unique message ID"""

        server_email = settings.SERVER_EMAIL

        _, domain = server_email.split('@')

        return f"{self.unique_id}@{domain}"

    def get_django_email(self, connection=None) -> EmailMessage:
        """Get a Django email message"""

        message_id = self.message_id

        # Django kwarg to related_address field key
        related_address_map = {
            'to': 'to',
            'cc': 'cc',
            'bcc': 'bcc',
            'reply_to': 'reply-to'
        }

        # Constructors are the same for both emails and email alternatives,
        # so do a little meta-programming and extract the commonalities
        kwargs = {
            'from_email': email.utils.formataddr((self.from_name, self.from_address)),
            'subject': self.subject,
            'body': self.text,
            'headers': {
                'Message-ID': message_id,
                'Date': email.utils.formatdate(self.created_at.timestamp())
            },
            'connection': connection,
        }

        # Load to/cc/bcc/reply-to
        all_addresses: List[RelatedAddress] = list(self.addresses.all())
        for mail_obj_key, addr_field_key in related_address_map.items():
            addresses = [addr for addr in all_addresses if addr.field == addr_field_key]
            kwargs[mail_obj_key] = [addr.encoded for addr in addresses]

        # Prune falsey values
        kwargs = {k: v for k, v in kwargs.items() if v}

        if self.html:
            msg = EmailMultiAlternatives(**kwargs)
            msg.attach_alternative(self.html, "text/html")
        else:
            msg = EmailMessage(**kwargs)

        return msg

    def __str__(self):
        return f"Message {self.pk}"


class RelatedAddress(models.Model):
    """Address to send an email to"""

    name = models.CharField(max_length=255)
    address = models.EmailField()
    message = models.ForeignKey(OutgoingMessage, on_delete=models.CASCADE, related_name='addresses')
    field = models.CharField(choices=FIELD_OPTIONS, max_length=_field_option_length)

    def __str__(self):
        if not self.name:
            return self.address

        return email.utils.formataddr((self.name, self.address))

    class Meta:
        unique_together = (
            ('address', 'message'),
        )

    @property
    def addr_obj(self) -> Address:
        """The address object to send from"""

        username, domain = self.address.split('@', 1)

        return Address(self.name, username, domain)

    @property
    def encoded(self) -> str:
        """An encoded address"""

        return email.utils.formataddr((self.name, self.address))
