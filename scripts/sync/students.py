"""Student reconciler"""

import manager


class StudentManager(manager.SyncManager):
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
