from datetime import date
import pytest

from uuid import uuid4

from blackbaud.models import (
    Teacher,
    Student,
    School,
    Course,
    Class,
    TeacherEnrollment,
    StudentEnrollment,
)
from blackbaud.students import teachers_for_students


@pytest.mark.django_db
def test_basic_student_teacher():
    middle_school = School()
    middle_school.name = "Middle school"
    middle_school.active = True
    middle_school.save()

    student = Student()
    student.sis_id = uuid4().hex
    student.active = True

    student.given_name = "Student"
    student.family_name = "1"
    student.email = "student1@example.org"
    student.grade = "9th grade"

    student.save()
    student.schools.add(middle_school)

    algebra = Course()
    algebra.sis_id = uuid4().hex
    algebra.active = True
    algebra.title = "Algebra"
    algebra.save()

    algebra_class = Class()
    algebra_class.sis_id = uuid4().hex
    algebra_class.active = True
    algebra_class.title = "Algebra ALG-123"
    algebra_class.course = algebra
    algebra_class.school = middle_school
    algebra_class.save()

    teacher = Teacher()
    teacher.sis_id = uuid4().hex
    teacher.active = True
    teacher.given_name = "Adam"
    teacher.family_name = "Peacock"
    teacher.email = "mr_peacock@example.org"
    teacher.save()
    teacher.schools.add(middle_school)

    jan_1 = date(2022, 1, 1)
    march_1 = date(2022, 3, 1)
    april_1 = date(2022, 5, 1)
    june_1 = date(2022, 6, 1)

    teacher_enrollment = TeacherEnrollment()
    teacher_enrollment.sis_id = uuid4().hex
    teacher_enrollment.active = True
    teacher_enrollment.teacher = teacher
    teacher_enrollment.section = algebra_class
    teacher_enrollment.teacher = teacher
    teacher_enrollment.school = middle_school
    teacher_enrollment.begin_date = jan_1
    teacher_enrollment.end_date = june_1
    teacher_enrollment.save()

    student_enrollment = StudentEnrollment()
    student_enrollment.sis_id = uuid4().hex
    student_enrollment.active = True
    student_enrollment.student = student
    student_enrollment.section = algebra_class
    student_enrollment.teacher = teacher
    student_enrollment.school = middle_school
    student_enrollment.begin_date = jan_1
    student_enrollment.end_date = june_1
    student_enrollment.save()

    actual = teachers_for_students([student], {march_1, april_1})
    expected = {(student, march_1): {teacher}, (student, april_1): {teacher}}

    assert actual == expected


@pytest.mark.django_db
def test_teacher_removed_on_date():
    middle_school = School()
    middle_school.name = "Middle school"
    middle_school.active = True
    middle_school.save()

    student = Student()
    student.sis_id = uuid4().hex
    student.active = True

    student.given_name = "Student"
    student.family_name = "1"
    student.email = "student1@example.org"
    student.grade = "9th grade"

    student.save()
    student.schools.add(middle_school)

    algebra = Course()
    algebra.sis_id = uuid4().hex
    algebra.active = True
    algebra.title = "Algebra"
    algebra.save()

    algebra_class = Class()
    algebra_class.sis_id = uuid4().hex
    algebra_class.active = True
    algebra_class.title = "Algebra ALG-123"
    algebra_class.course = algebra
    algebra_class.school = middle_school
    algebra_class.save()

    adam = Teacher()
    adam.sis_id = uuid4().hex
    adam.active = True
    adam.given_name = "Adam"
    adam.family_name = "Peacock"
    adam.email = "mr_peacock@example.org"
    adam.save()
    adam.schools.add(middle_school)

    lisa = Teacher()
    lisa.sis_id = uuid4().hex
    lisa.active = True
    lisa.given_name = "Lisa"
    lisa.family_name = "Hart"
    lisa.email = "mrs_hart@example.org"
    lisa.save()
    lisa.schools.add(middle_school)

    jan_1 = date(2022, 1, 1)
    march_1 = date(2022, 3, 1)
    april_1 = date(2022, 5, 1)
    june_1 = date(2022, 6, 1)

    adam_enrollment = TeacherEnrollment()
    adam_enrollment.sis_id = uuid4().hex
    adam_enrollment.active = True
    adam_enrollment.teacher = adam
    adam_enrollment.section = algebra_class
    adam_enrollment.school = middle_school
    adam_enrollment.begin_date = jan_1
    adam_enrollment.end_date = june_1
    adam_enrollment.save()

    lisa_enrollment = TeacherEnrollment()
    lisa_enrollment.sis_id = uuid4().hex
    lisa_enrollment.active = True
    lisa_enrollment.teacher = lisa
    lisa_enrollment.section = algebra_class
    lisa_enrollment.school = middle_school
    lisa_enrollment.begin_date = jan_1
    lisa_enrollment.end_date = march_1
    lisa_enrollment.save()

    student_enrollment = StudentEnrollment()
    student_enrollment.sis_id = uuid4().hex
    student_enrollment.active = True
    student_enrollment.student = student
    student_enrollment.section = algebra_class
    student_enrollment.teacher = adam
    student_enrollment.school = middle_school
    student_enrollment.begin_date = jan_1
    student_enrollment.end_date = june_1
    student_enrollment.save()

    actual = teachers_for_students([student], {march_1, april_1})

    # Adam was teaching from Jan 1 to June 1. Lisa was teaching from Jan 1 to March 1
    expected = {(student, march_1): {adam, lisa}, (student, april_1): {adam}}

    assert actual == expected
