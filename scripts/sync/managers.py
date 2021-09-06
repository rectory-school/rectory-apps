"""Student reconciler"""

import logging

from manager import SyncManager
from parsers import active_parse

log = logging.getLogger(__name__)


class StudentManager(SyncManager):
    apps_url_key = 'students'
    apps_key = 'student_id'
    ks_key = 'IDSTUDENT'
    field_map = [
        ('student_id', 'IDSTUDENT'),
        ('first_name', 'NameFirst'),
        ('last_name', 'NameLast'),
        ('nickname', 'NameNickname'),
        ('email', 'EMailSchool'),
        ('gender', 'Sex'),
    ]


class TeacherManager(SyncManager):
    apps_url_key = 'teachers'
    apps_key = 'teacher_id'
    ks_key = 'IDTEACHER'

    field_map = [
        ('teacher_id', 'IDTEACHER'),
        ('unique_name', 'NameUnique'),
        ('first_name', 'NameFirst'),
        ('last_name', 'NameLast'),
        ('prefix', 'NamePrefix'),
        ('email', 'EmailSchool'),
        ('active', 'Active Employee'),
    ]

    field_translations = {
        'active': active_parse,
    }


class CourseManager(SyncManager):
    apps_url_key = 'courses'
    apps_key = 'number'
    ks_key = 'CourseNumber'

    field_map = [
        ('number', 'CourseNumber'),
        ('course_name', 'CourseName'),
        ('course_name_short', 'CourseNameShort'),
        ('course_name_transcript', 'CourseNameTranscript'),
        ('division', 'Division'),
        ('grade_level', 'GradeLevel'),
        ('department', 'DepartmentName'),
        ('course_type', 'CourseType'),
    ]
