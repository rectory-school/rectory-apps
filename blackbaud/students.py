"""Calculations about students"""

from collections import defaultdict
from datetime import date
from typing import DefaultDict, Dict, Iterable, Sequence, Set, Tuple
from blackbaud.models import (
    Student,
    Teacher,
    StudentEnrollment,
    TeacherEnrollment,
    Class,
)


def teachers_for_students(
    students: Iterable[Student], dates: Set[date]
) -> Dict[Tuple[Student, date], Set[Teacher]]:
    """Get the teachers that a relevant to a collection
    of students for a set of given dates"""

    student_enrollments: Iterable[StudentEnrollment] = StudentEnrollment.objects.filter(
        student__in=students
    )
    students_by_id: Dict[int, Student] = {obj.pk: obj for obj in students}

    relevant_class_ids: Set[int] = {e.section_id for e in student_enrollments}

    relevant_classes: Iterable[Class] = Class.objects.filter(pk__in=relevant_class_ids)

    teacher_enrollments: Iterable[TeacherEnrollment] = TeacherEnrollment.objects.filter(
        section_id__in=relevant_class_ids
    )
    teachers: Iterable[Teacher] = Teacher.objects.filter(
        enrollments__in=teacher_enrollments
    )

    teachers_by_id = {obj.pk: obj for obj in teachers}

    teacher_enrollments_by_section_id: DefaultDict[int, Set[TeacherEnrollment]] = (
        defaultdict(set)
    )
    student_enrollments_by_section_id: DefaultDict[int, Set[StudentEnrollment]] = (
        defaultdict(set)
    )

    for e_teacher in teacher_enrollments:
        teacher_enrollments_by_section_id[e_teacher.section_id].add(e_teacher)

    for e_student in student_enrollments:
        student_enrollments_by_section_id[e_student.section_id].add(e_student)

    # Pre-create the return dictionary so we are guaranteed
    # to have every student/date pair for return
    out: Dict[Tuple[Student, date], Set[Teacher]] = {
        (s, d): set() for s in students for d in dates
    }

    for section in relevant_classes:
        section_id: int = section.pk
        s_e_objs = student_enrollments_by_section_id[section_id]
        t_e_objs = teacher_enrollments_by_section_id[section_id]

        for d in dates:
            for s_e in s_e_objs:
                student_id = s_e.student_id
                student = students_by_id[student_id]

                if s_e.begin_date <= d and d <= s_e.end_date:
                    for t_e in t_e_objs:
                        teacher_id = t_e.teacher_id
                        teacher = teachers_by_id[teacher_id]
                        if t_e.begin_date <= d and d <= t_e.end_date:
                            out[(student, d)].add(teacher)

    return out
