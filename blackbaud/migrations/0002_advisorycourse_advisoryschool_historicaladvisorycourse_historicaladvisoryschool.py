# Generated by Django 3.2.15 on 2022-09-16 15:27

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import simple_history.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("blackbaud", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="HistoricalAdvisorySchool",
            fields=[
                (
                    "id",
                    models.BigIntegerField(
                        auto_created=True, blank=True, db_index=True, verbose_name="ID"
                    ),
                ),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_date", models.DateTimeField(db_index=True)),
                ("history_change_reason", models.CharField(max_length=100, null=True)),
                (
                    "history_type",
                    models.CharField(
                        choices=[("+", "Created"), ("~", "Changed"), ("-", "Deleted")],
                        max_length=1,
                    ),
                ),
                (
                    "history_user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "school",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        limit_choices_to={"active": True},
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="blackbaud.school",
                    ),
                ),
            ],
            options={
                "verbose_name": "historical advisory school",
                "verbose_name_plural": "historical advisory schools",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name="HistoricalAdvisoryCourse",
            fields=[
                (
                    "id",
                    models.BigIntegerField(
                        auto_created=True, blank=True, db_index=True, verbose_name="ID"
                    ),
                ),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_date", models.DateTimeField(db_index=True)),
                ("history_change_reason", models.CharField(max_length=100, null=True)),
                (
                    "history_type",
                    models.CharField(
                        choices=[("+", "Created"), ("~", "Changed"), ("-", "Deleted")],
                        max_length=1,
                    ),
                ),
                (
                    "course",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        limit_choices_to={"active": True},
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="blackbaud.course",
                    ),
                ),
                (
                    "history_user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "historical advisory course",
                "verbose_name_plural": "historical advisory courses",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name="AdvisorySchool",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "school",
                    models.OneToOneField(
                        limit_choices_to={"active": True},
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="advisory_schools",
                        to="blackbaud.school",
                    ),
                ),
            ],
            options={
                "ordering": ["school"],
            },
        ),
        migrations.CreateModel(
            name="AdvisoryCourse",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "course",
                    models.OneToOneField(
                        limit_choices_to={"active": True},
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="advisory_course",
                        to="blackbaud.course",
                    ),
                ),
            ],
            options={
                "ordering": ["course"],
                "permissions": (
                    ("view_advisor_list_report", "Can view advisor list reports"),
                ),
            },
        ),
    ]
