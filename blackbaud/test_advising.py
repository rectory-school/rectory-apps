from datetime import date, timedelta
import pytest
from uuid import uuid4

import blackbaud.models

from blackbaud import advising


@pytest.mark.django_db
def test_get_advisees():
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

    assert list(advising.get_advisory_courses()) == [course]


@pytest.mark.django_db
def test_get_advisory_courses():
    course = blackbaud.models.Course(
        sis_id=uuid4().hex,
        active=True,
        title="Advisory",
    )
    course.save()

    blackbaud.models.AdvisoryCourse.objects.create(course=course)

    assert list(advising.get_advisory_courses()) == [course]
