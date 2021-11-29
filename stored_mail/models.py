"""Models for stored mail sender"""

import email.utils
import email.message
from email.headerregistry import Address
from uuid import uuid4

from django.db import models
from django.conf import settings

FIELD_OPTIONS = (
    ('to', 'To'),
    ('cc', 'Cc'),
    ('bcc', 'Bcc'),
)

_field_option_length = max((len(o[0]) for o in FIELD_OPTIONS))


class OutgoingMessage(models.Model):
    """Outgoing email stored for sending"""

    unique_id = models.UUIDField(default=uuid4, unique=True)

    from_name = models.CharField(max_length=255)
    from_address = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    subject = models.CharField(max_length=4096, blank=True)
    text = models.TextField()
    html = models.TextField(blank=True)

    sent_at = models.DateTimeField(null=True)

    @ property
    def message_id(self) -> str:
        """Unique message ID"""

        server_email = settings.SERVER_EMAIL

        _, domain = server_email.split('@')

        return f"{self.unique_id}@{domain}"

    def get_mime(self) -> email.message.EmailMessage:
        msg = email.message.EmailMessage()

        try:
            domain = settings.MAILGUN_SENDER_DOMAIN
        except AttributeError:
            domain = None

        msg['Message-ID'] = self.message_id
        msg['From'] = self.from_addr_obj

        if self.subject:
            msg['Subject'] = self.subject

        to_addrs = [addr.addr_obj for addr in self.addresses.all() if addr.field == 'to']
        cc_addrs = [addr.addr_obj for addr in self.addresses.all() if addr.field == 'cc']
        bcc_addrs = [addr.addr_obj for addr in self.addresses.all() if addr.field == 'bcc']

        if to_addrs:
            msg['To'] = to_addrs

        if cc_addrs:
            msg['Cc'] = cc_addrs

        if bcc_addrs:
            msg['Bcc'] = bcc_addrs

        msg.set_content(self.text)
        if self.html:
            msg.add_alternative(self.html, subtype='html')

        return msg

    def __str__(self):
        return self.subject

    def mime_text(self) -> str:
        return str(self.get_mime())

    @ property
    def from_addr_obj(self) -> Address:
        """The address object to send from"""

        username, domain = self.from_address.split('@', 1)

        return Address(self.from_name, username, domain)


class SendAddress(models.Model):
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

    @ property
    def addr_obj(self) -> Address:
        """The address object to send from"""

        username, domain = self.address.split('@', 1)

        return Address(self.name, username, domain)
