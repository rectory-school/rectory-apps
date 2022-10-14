"""Tests for the email system"""

from datetime import date, time, datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.db import transaction
from django.template import TemplateDoesNotExist

import blackbaud.models

from enrichment.models import (
    EmailConfig,
    RelatedAddress,
    Option,
    Signup,
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
    blackbaud.models.AdvisoryCourse.objects.all().delete()
    blackbaud.models.AdvisorySchool.objects.all().delete()

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

    student_jimmy = blackbaud.models.Student(
        sis_id=uuid4().hex,
        active=True,
        given_name="Jimmy",
        family_name="Neutron",
        email="example@example.org",
    )
    student_jimmy.save()
    student_jimmy.schools.add(middle_school)

    student_peachick = blackbaud.models.Student(
        sis_id=uuid4().hex,
        active=True,
        given_name="Little",
        family_name="Peachick",
        email="example@example.org",
    )
    student_peachick.save()
    student_peachick.schools.add(middle_school)

    teacher_peacock = blackbaud.models.Teacher(
        sis_id=uuid4().hex,
        active=True,
        given_name="Adam",
        family_name="Peacock",
        email="example@example.org",
    )
    teacher_peacock.save()

    teacher_ryan = blackbaud.models.Teacher(
        sis_id=uuid4().hex,
        active=True,
        given_name="Ryan",
        family_name="Reynolds",
        email="example@example.org",
    )
    teacher_ryan.save()

    peacock_section_advising = blackbaud.models.Class(
        sis_id=uuid4().hex,
        active=True,
        title="Peacock advising",
        course=course,
        school=middle_school,
    )
    peacock_section_advising.save()

    blackbaud.models.TeacherEnrollment.objects.create(
        sis_id=uuid4().hex,
        active=True,
        section=peacock_section_advising,
        teacher=teacher_peacock,
        school=middle_school,
        begin_date=date.today() - timedelta(days=30),
        end_date=date.today() + timedelta(days=30),
    )

    blackbaud.models.StudentEnrollment.objects.create(
        sis_id=uuid4().hex,
        active=True,
        section=peacock_section_advising,
        student=student_jimmy,
        school=middle_school,
        begin_date=date.today() - timedelta(days=30),
        end_date=date.today() + timedelta(days=30),
    )

    blackbaud.models.StudentEnrollment.objects.create(
        sis_id=uuid4().hex,
        active=True,
        section=peacock_section_advising,
        student=student_peachick,
        school=middle_school,
        begin_date=date.today() - timedelta(days=30),
        end_date=date.today() + timedelta(days=30),
    )

    blackbaud.models.AdvisoryCourse.objects.create(course=course)
    blackbaud.models.AdvisorySchool.objects.create(school=middle_school)

    slot = Slot()
    slot.date = date(2000, 1, 1)
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

    option_peacock = Option()
    option_peacock.start_date = date(1999, 1, 1)
    option_peacock.end_date = option_peacock.start_date + timedelta(days=3650)
    option_peacock.teacher = teacher_peacock
    option_peacock.save()

    option_reynolds = Option()
    option_reynolds.start_date = date(1999, 1, 1)
    option_reynolds.end_date = option_peacock.start_date + timedelta(days=3650)
    option_reynolds.teacher = teacher_ryan
    option_reynolds.location = "The MCU"
    option_reynolds.save()

    signup_jimmy = Signup()
    signup_jimmy.slot = slot
    signup_jimmy.option = option_reynolds
    signup_jimmy.student = student_jimmy
    signup_jimmy.admin_locked = False
    signup_jimmy.save()

    signup_peachick = Signup()
    signup_peachick.slot = slot
    signup_peachick.option = option_reynolds
    signup_peachick.student = student_peachick
    signup_peachick.admin_locked = False
    signup_peachick.save()

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
                try:
                    html = msg.message_html
                    with open(
                        f"scratch/email-sample/{msg.cfg.report}_{i}.html", "w"
                    ) as f_out:
                        f_out.write(html)
                except TemplateDoesNotExist:
                    print(f"Did not have html template for {cfg.report}")

                try:
                    text = msg.message_text
                    with open(
                        f"scratch/email-sample/{msg.cfg.report}_{i}.txt", "w"
                    ) as f_out:
                        f_out.write(text)
                except TemplateDoesNotExist:
                    print(f"Did not have text template for {cfg.report}")
        except KeyError:
            print(f"Did not have backing keys for {cfg.report}")
