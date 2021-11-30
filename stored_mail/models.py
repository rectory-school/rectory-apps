"""Models for stored mail sender"""

from typing import Optional

import email.utils
import email.message
from email.headerregistry import Address
from uuid import uuid4

from django.db import models
from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives

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

    reply_to_name = models.CharField(max_length=255)
    reply_to_address = models.EmailField()

    created_at = models.DateTimeField(auto_now_add=True)

    subject = models.CharField(max_length=4096, blank=True)
    text = models.TextField()
    html = models.TextField(blank=True)

    sent_at = models.DateTimeField(null=True)

    @property
    def message_id(self) -> str:
        """Unique message ID"""

        server_email = settings.SERVER_EMAIL

        _, domain = server_email.split('@')

        return f"{self.unique_id}@{domain}"

    def get_mime(self) -> email.message.EmailMessage:
        """Get a MIME message"""
        msg = email.message.EmailMessage()

        msg['Message-ID'] = self.message_id
        msg['From'] = self.from_addr_obj

        if self.reply_to_addr_obj:
            msg['Reply-To'] = self.reply_to_addr_obj

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

    def get_django_email(self) -> EmailMessage:
        """Get a Django email message"""

        to_addrs = [addr.encoded for addr in self.addresses.all() if addr.field == 'to']
        cc_addrs = [addr.encoded for addr in self.addresses.all() if addr.field == 'cc']
        bcc_addrs = [addr.encoded for addr in self.addresses.all() if addr.field == 'bcc']

        if self.html:
            msg = EmailMultiAlternatives()
            msg.attach_alternative(self.html, "text/html")
        else:
            msg = EmailMessage()

        msg.subject = self.subject
        msg.body = self.text
        msg.from_email = self.from_addr_encoded
        msg.to = to_addrs
        msg.cc = cc_addrs
        msg.bcc = bcc_addrs
        if self.reply_to_addr_encoded:
            msg.reply_to = [self.reply_to_addr_encoded]

        return msg

    def __str__(self):
        return f"Message {self.pk}"

    @property
    def from_addr_obj(self) -> Address:
        """The address object to send from"""

        username, domain = self.from_address.split('@', 1)

        return Address(self.from_name, username, domain)

    @property
    def from_addr_encoded(self) -> str:
        """Encoded from address"""

        return email.utils.formataddr((self.from_name, self.from_address))

    @property
    def reply_to_addr_obj(self) -> Optional[Address]:
        """Address object for the reply to"""

        if not self.reply_to_address:
            return None

        username, domain = self.reply_to_address.split('@', 1)
        return Address(self.reply_to_name, username, domain)

    @property
    def reply_to_addr_encoded(self) -> Optional[str]:
        """Encoded reply to address"""

        if self.reply_to_address:
            return email.utils.formataddr((self.reply_to_name, self.reply_to_address))

        return None


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

    @property
    def addr_obj(self) -> Address:
        """The address object to send from"""

        username, domain = self.address.split('@', 1)

        return Address(self.name, username, domain)

    @property
    def encoded(self) -> str:
        """An encoded address"""

        return email.utils.formataddr((self.name, self.address))
