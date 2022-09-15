"""SIS Sync command"""

from django.core.management.base import BaseCommand
from blackbaud.sync import auto_sync


class Command(BaseCommand):
    help = "Run SIS sync job"

    def handle(self, *args, **opts):
        auto_sync(True)
