"""Permission dump"""

from typing import Iterable
from django.core.management.base import BaseCommand

from django.contrib.auth.models import Permission


class Command(BaseCommand):
    help = "Dump permissions to command line"

    def handle(self, *args, **opts):
        permissions: Iterable[Permission] = (
            Permission.objects.all()
            .select_related("content_type")
            .order_by(
                "content_type__app_label",
                "content_type__model",
                "codename",
            )
        )

        for perm in permissions:
            content_type = perm.content_type
            app_label = content_type.app_label

            print(f"{app_label}.{perm.codename}: {perm}")
