"""Tests for the email system"""

from datetime import date, time, datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.db import transaction

import blackbaud.models

from enrichment.models import (
    EmailConfig,
    RelatedAddress,
    Option,
    Slot,
    EMAIL_REPORT_CHOICES,
    RELATED_ADDRESS_CHOICES,
)
from enrichment.emails import get_outgoing_messages


class Rollback(Exception):
    """Exception to trigger a rollback"""


class Command(BaseCommand):
    help = "Make all the sample emails"

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                _make_samples()
                raise Rollback()
        except Rollback:
            pass


def _make_samples():
    middle_school = blackbaud.models.School(
        sis_id=uuid4().hex,
        active=True,
        name="Middle School",
    )
    middle_school.save()

    course = blackbaud.models.Course(
        sis_id=uuid4().hex,
        active=True,
        title="Advisory",
    )
    course.save()

    student = blackbaud.models.Student(
        sis_id=uuid4().hex,
        active=True,
        given_name="Jimmy",
        family_name="Neutron",
        email="example@example.org",
    )
    student.save()
    student.schools.add(middle_school)

    teacher = blackbaud.models.Teacher(
        sis_id=uuid4().hex,
        active=True,
        given_name="Adam",
        family_name="Peacock",
        email="example@example.org",
    )
    teacher.save()

    section = blackbaud.models.Class(
        sis_id=uuid4().hex,
        active=True,
        title="Peacock advising",
        course=course,
        school=middle_school,
    )
    section.save()

    blackbaud.models.TeacherEnrollment.objects.create(
        sis_id=uuid4().hex,
        active=True,
        section=section,
        teacher=teacher,
        school=middle_school,
        begin_date=date.today() - timedelta(days=30),
        end_date=date.today() + timedelta(days=30),
    )

    blackbaud.models.StudentEnrollment.objects.create(
        sis_id=uuid4().hex,
        active=True,
        section=section,
        student=student,
        school=middle_school,
        begin_date=date.today() - timedelta(days=30),
        end_date=date.today() + timedelta(days=30),
    )

    blackbaud.models.AdvisoryCourse.objects.create(course=course)
    blackbaud.models.AdvisorySchool.objects.create(school=middle_school)

    slot = Slot()
    slot.date = date(2022, 10, 11)  # Tuesday
    slot.editable_until = datetime(
        slot.date.year,
        slot.date.month,
        slot.date.day,
        12,
        0,
        0,
        0,
        ZoneInfo("America/New_York"),
    )
    slot.save()

    option = Option()
    option.start_date = date.today() - timedelta(days=7)
    option.end_date = option.start_date + timedelta(days=365)

    option.teacher = teacher
    option.save()

    cfgs: list[EmailConfig] = []

    for report_name, _ in EMAIL_REPORT_CHOICES:
        cfg = EmailConfig()
        cfg.report = report_name
        cfg.start = 0
        cfg.end = 0
        cfg.time = time(11, 0, 0)
        cfg.monday = True
        cfg.tuesday = True
        cfg.wednesday = True
        cfg.thursday = True
        cfg.friday = True
        cfg.saturday = True
        cfg.sunday = True

        cfg.from_name = "Rectory Enrichment System"
        cfg.from_address = "server@apps.rectoryschool.org"

        cfg.save()
        cfgs.append(cfg)

        for addr_type, _ in RELATED_ADDRESS_CHOICES:
            RelatedAddress.objects.create(
                name=f"Sample related: {addr_type}",
                address=f"{addr_type}@example.org",
                field=addr_type,
                message=cfg,
            )

    for cfg in cfgs:
        try:
            msgs = get_outgoing_messages(cfg, slot.date)

            for i, msg in enumerate(msgs):
                with open(
                    f"scratch/email-sample/{msg.cfg.report}_{i}.html", "w"
                ) as f_out:
                    f_out.write(msg.message_html)

                with open(
                    f"scratch/email-sample/{msg.cfg.report}_{i}.txt", "w"
                ) as f_out:
                    f_out.write(msg.message_text)
        except KeyError:
            print(f"Did not have backing keys for {cfg}")
