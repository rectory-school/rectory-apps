# Generated by Django 4.2.14 on 2024-07-24 15:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("enrichment", "0011_alter_signup_options"),
    ]

    operations = [
        migrations.AlterField(
            model_name="option",
            name="not_available_on",
            field=models.ManyToManyField(
                blank=True,
                help_text="A list of slots this option should not be available on",
                related_name="+",
                to="enrichment.slot",
            ),
        ),
        migrations.AlterField(
            model_name="option",
            name="only_available_on",
            field=models.ManyToManyField(
                blank=True,
                help_text="An exclusive list of slots this option should be available on",
                related_name="+",
                to="enrichment.slot",
            ),
        ),
    ]