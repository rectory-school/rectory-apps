"""Advisory helper methods"""

from datetime import date
from typing import Iterable, NamedTuple, Optional, Set, Tuple

from blackbaud.models import School, Teacher, Student, Course, Class

from django.db.models import QuerySet


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
) -> Set[AdviseePair]:
    """Get the advisee/advisor pairs for a given set of students and/or teachers"""

    advisory_sections = get_advisory_sections().prefetch_related("students", "teachers")

    school_students = Student.objects.filter(schools__in=get_advisory_schools())
    advisory_sections = advisory_sections.filter(students__in=school_students)

    if limit_teachers:
        advisory_sections = advisory_sections.filter(teachers__in=limit_teachers)

    if limit_students:
        advisory_sections = advisory_sections.filter(students__in=limit_students)

    pairs: Set[AdviseePair] = set()

    for section in advisory_sections:
        for teacher in section.teachers.all():
            for student in section.students.all():
                pairs.add(
                    AdviseePair(
                        teacher=teacher,
                        student=student,
                    )
                )

    return pairs
