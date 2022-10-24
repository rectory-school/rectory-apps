"""Advisory helper methods"""

from datetime import date
from typing import Iterable, NamedTuple, Optional

from blackbaud.models import (
    School,
    StudentEnrollment,
    Teacher,
    Student,
    Course,
    Class,
    TeacherEnrollment,
)

from django.db.models import QuerySet
from django.utils import timezone


class AdviseePair(NamedTuple):
    student: Student
    teacher: Teacher


def get_advisory_courses() -> QuerySet[Course]:
    return Course.objects.filter(
        advisory_course__isnull=False,
        active=True,
    )


def get_advisory_sections() -> QuerySet[Class]:
    courses = get_advisory_courses()

    return Class.objects.filter(
        course__in=courses,
        active=True,
    )


def get_advisory_schools() -> QuerySet[School]:
    return School.objects.filter(advisory_schools__isnull=False, active=True)


def get_advisees(
    limit_teachers: Optional[Iterable[Teacher]] = None,
    limit_students: Optional[Iterable[Student]] = None,
    as_of: Optional[date] = None,
) -> set[AdviseePair]:
    """Get the advisee/advisor pairs for a given set of students and/or teachers"""

    if not as_of:
        as_of = timezone.now().date()

    advisory_sections = get_advisory_sections().prefetch_related(
        "students",
        "teachers",
        "student_enrollments",
        "teacher_enrollments",
        "student_enrollments__student",
        "teacher_enrollments__teacher",
    )

    school_students = Student.objects.filter(schools__in=get_advisory_schools())
    advisory_sections = advisory_sections.filter(students__in=school_students)

    if limit_teachers is not None:
        advisory_sections = advisory_sections.filter(teachers__in=limit_teachers)

    if limit_students is not None:
        advisory_sections = advisory_sections.filter(students__in=limit_students)

    pairs: set[AdviseePair] = set()

    for section in advisory_sections:
        for teacher_enrollment in section.teacher_enrollments.all():
            assert isinstance(teacher_enrollment, TeacherEnrollment)
            if (
                teacher_enrollment.begin_date <= as_of
                and as_of <= teacher_enrollment.end_date
            ):
                for student_enrollment in section.student_enrollments.all():
                    assert isinstance(student_enrollment, StudentEnrollment)

                    if (
                        student_enrollment.begin_date <= as_of
                        and as_of <= student_enrollment.end_date
                    ):
                        pairs.add(
                            AdviseePair(
                                teacher=teacher_enrollment.teacher,
                                student=student_enrollment.student,
                            )
                        )

    return pairs


def get_advisees_by_advisors(
    limit_teachers: Optional[Iterable[Teacher]] = None,
    limit_students: Optional[Iterable[Student]] = None,
) -> dict[Teacher, set[Student]]:

    out: dict[Teacher, set[Student]] = {}

    for pair in get_advisees(limit_teachers, limit_students):
        if not pair.teacher in out:
            out[pair.teacher] = set()

        out[pair.teacher].add(pair.student)

    return out
