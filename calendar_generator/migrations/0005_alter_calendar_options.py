# Generated by Django 3.2.5 on 2021-07-19 18:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("calendar_generator", "0004_auto_20210716_0216"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="calendar",
            options={"ordering": ["-start_date"]},
        ),
    ]
