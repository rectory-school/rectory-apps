# Generated by Django 3.2.5 on 2021-07-14 17:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("calendar_generator", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="day",
            name="position",
            field=models.PositiveIntegerField(blank=True, default=0, null=True),
        ),
    ]
