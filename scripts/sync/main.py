#!/usr/bin/env python

"""SIS sync script"""

import argparse
import logging

from students import StudentManager
from teachers import TeacherManager

logging.basicConfig(level=logging.INFO)

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# The following files can be managed directly with no foreign keys:
# students
# teachers
# courses


def main():
    """Main entrypoint"""

    parser = argparse.ArgumentParser()
    parser.add_argument("--student-file", default="ksPERMRECS.xml.json")
    parser.add_argument("--teacher-file", default="ksTEACHERS.xml.json")
    parser.add_argument("--course-file", default="ksCOURSES.xml.json")
    parser.add_argument("--api-root", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)

    args = parser.parse_args()
    auth = (args.username, args.password)

    students = StudentManager(args.api_root, auth=auth, ks_filename=args.student_file)
    students.create()

    teachers = TeacherManager(args.api_root, auth=auth, ks_filename=args.teacher_file)
    teachers.create()


if __name__ == "__main__":
    main()
