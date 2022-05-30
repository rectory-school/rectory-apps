from datetime import timedelta
from django.db import migrations, models
from django_safemigrate import Safe


def set_discard_after(apps, schema_editor):
    """Set the discard_after values"""

    del schema_editor

    OutgoingMessage = apps.get_model("stored_mail", "OutgoingMessage")
    unset = OutgoingMessage.objects.filter(discard_after__isnull=True)
    unset.update(discard_after=models.F("created_at") + timedelta(days=7))


class Migration(migrations.Migration):
    safe = Safe.always

    dependencies = [
        ("stored_mail", "0002_outgoingmessage_discard_after"),
    ]

    operations = [
        migrations.RunPython(set_discard_after, migrations.RunPython.noop),
    ]
