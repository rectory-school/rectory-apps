"""SIS data sync models"""

import logging
from random import choice
from django.db import models

log = logging.getLogger(__name__)


class AcademicYear(models.Model):
    """An academic year, such as 2019-2020"""

    year = models.CharField(max_length=9, unique=True)
    current = models.BooleanField(default=False)

    class Meta:
        ordering = ['year']

    def __str__(self):
        return self.year


class Student(models.Model):
    """A student, such as John Doe"""

    # Keystone table: ksPERMRECS

    student_id = models.CharField(max_length=7, unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    nickname = models.CharField(max_length=255, blank=True)
    email = models.EmailField(max_length=255, blank=True)
    current = models.BooleanField(default=False)

    rectory_password = models.CharField(max_length=254, blank=True)
    username = models.CharField(max_length=254, blank=True)

    gender = models.CharField(max_length=1, blank=True, default="")

    parents = models.ManyToManyField('Parent', through='StudentParentRelation', blank=True)

    class Meta:
        ordering = ('last_name', 'first_name')

    @property
    def name(self):
        """Name as 'John Doe'"""

        if self.nickname:
            return f"{self.first_name} ({self.nickname}) {self.last_name}"

        return f"{self.first_name} {self.last_name}"

    @property
    def last_name_first(self):
        """Name as 'Doe, John'"""

        if self.nickname:
            return f"{self.last_name}, {self.first_name} ({self.nickname})"

        return f"{self.last_name}, {self.first_name}"

    def __str__(self):
        return self.name


class Teacher(models.Model):
    """A teacher, such as Adam Peacock"""

    # Keystone table: ksTEACHERS
    teacher_id = models.CharField(max_length=5, unique=True)
    unique_name = models.CharField(max_length=255)

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    prefix = models.CharField(max_length=255, blank=True)

    email = models.EmailField(max_length=255, blank=True)
    active = models.BooleanField(default=False)

    class Meta:
        ordering = ['last_name', 'first_name']

    @property
    def name(self):
        """Name such as Adam Peacock"""

        return f"{self.first_name} {self.last_name}"

    @property
    def name_for_students(self):
        """Name such as 'Mr. Peacock'"""

        if self.prefix and self.last_name:
            return f"{self.prefix} {self.last_name}"

        elif self.first_name and self.last_name:
            return f"{self.last_name}, {self.first_name}"

        elif self.last_name:
            return f"M. {self.last_name}"

        else:
            return f"Teacher {self.teacher_id}"

    def __str__(self):
        return self.name


class Dorm(models.Model):
    """A dorm, such as Hamilton North 2"""

    dorm_name = models.CharField(max_length=20, unique=True)

    building = models.CharField(max_length=20)
    wing = models.CharField(max_length=20, blank=True)
    level = models.CharField(max_length=20, blank=True)

    heads = models.ManyToManyField(Teacher,
                                   related_name="+",
                                   limit_choices_to={'active': True},
                                   blank=True,
                                   verbose_name="dorm parents")

    class Meta:
        ordering = ['building', 'wing', 'level']

    def __str__(self):
        if self.wing and self.level:
            return f"{self.building} {self.level} {self.wing}"

        elif self.wing:
            return f"{self.building} {self.wing}"

        elif self.level:
            return f"{self.level} {self.building}"

        else:
            return self.building


class Grade(models.Model):
    """A grade, such as 8th"""

    SCHOOL_CHOICES = (('', '--'),
                      ('elementary', 'Elementary School'),
                      ('middle', 'Middle School'),
                      ('high', 'High School'))

    SCHOOL_CHOICES_LENGTH = max(len(choice[0]) for choice in SCHOOL_CHOICES)

    grade = models.CharField(max_length=2, unique=True)
    description = models.CharField(max_length=63, unique=True)

    school = models.CharField(max_length=SCHOOL_CHOICES_LENGTH, choices=SCHOOL_CHOICES, default='', blank=True)

    class Meta:
        ordering = ['grade']

    def __str__(self):
        return self.description


class Enrollment(models.Model):
    """An enrollment, such as John Doe in 2019-2020"""

    # Keystone table: ksEnrollment

    student = models.ForeignKey(Student)
    academic_year = models.ForeignKey(AcademicYear)
    boarder = models.BooleanField()
    dorm = models.ForeignKey(Dorm, blank=True, null=True)
    grade = models.ForeignKey(Grade, null=True)
    division = models.CharField(max_length=2)
    section = models.CharField(max_length=1, blank=True)
    advisor = models.ForeignKey(Teacher, blank=True, null=True)
    status_enrollment = models.CharField(max_length=20, blank=True)
    status_attending = models.CharField(max_length=20, blank=True)

    enrolled_date = models.DateField(blank=True, null=True)

    class Meta:
        unique_together = (('student', 'academic_year'), )
        ordering = ['student__last_name', 'student__first_name', 'academic_year__year']

    def __str__(self):
        return f"{self.student.name} ({self.academic_year.year})"


class Course(models.Model):
    """A course, such as geometry"""

    # Keystone table: ksCOURSES

    number = models.CharField(max_length=20, unique=True)
    course_name = models.CharField(max_length=255)
    course_name_short = models.CharField(max_length=255)
    course_name_transcript = models.CharField(max_length=255)
    division = models.CharField(max_length=2)
    grade_level = models.CharField(max_length=2, blank=True)
    department = models.CharField(max_length=255)
    course_type = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.number}: {self.course_name}"


class Section(models.Model):
    """A course section, such as Geometry 01"""

    # Keystone table: ksSECTIONS

    course = models.ForeignKey(Course)
    csn = models.CharField(max_length=255)
    academic_year = models.ForeignKey(AcademicYear)
    teacher = models.ForeignKey(Teacher, blank=True, null=True)

    students = models.ManyToManyField(Student, through='StudentRegistration')

    class Meta:
        unique_together = (('csn', 'academic_year'), )

    def __str__(self):
        return f"{self.csn} ({self.academic_year.year})"


class StudentRegistration(models.Model):
    """A student registration, such as 'John Doe in Geometry 01'"""

    # TODO: Validate this keystone table
    # Keystone table: ksSTUREG

    student_reg_id = models.CharField(max_length=20, unique=True)

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)

    def __str__(self):
        return "{section:}: {student:}".format(section=self.section, student=self.student)


class Parent(models.Model):
    """A parent, such as Jane Doe"""

    PARENT_ID_CHOICES = (('Pa', 'Parent A'), ('Pb', 'Parent B'))
    PARENT_ID_LENGTH = max(len(choice[0]) for choice in PARENT_ID_CHOICES)

    family_id = models.CharField(max_length=20)
    parent_id = models.CharField(max_length=PARENT_ID_LENGTH)

    full_id = models.CharField(max_length=(20 + PARENT_ID_LENGTH), unique=True)

    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)

    email = models.EmailField(max_length=254, blank=True)
    phone_home = models.CharField(max_length=100, blank=True)
    phone_work = models.CharField(max_length=100, blank=True)
    phone_cell = models.CharField(max_length=100, blank=True)

    address = models.TextField(blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    @property
    def name(self):
        return f"self.first_name self.last_name"

    def __str__(self):
        return self.name


class StudentParentRelation(models.Model):
    """A student parent relationship, such as Jane Doe/John Doe"""

    student = models.ForeignKey(Student, db_index=True)
    parent = models.ForeignKey(Parent, db_index=True)

    relationship = models.CharField(max_length=20, blank=True)
    family_id_key = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.student}/{self.parent}"

    class Meta:
        unique_together = (('student', 'parent'), )
