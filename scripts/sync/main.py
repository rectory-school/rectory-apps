#!/usr/bin/env python

"""SIS sync script"""

import argparse
import logging

from requests_futures.sessions import FuturesSession

from students import StudentManager

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

    session = FuturesSession()
    session.auth = (args.username, args.password)

    url_map = session.get(args.api_root).result().json()

    students = StudentManager(session, url_map, args.student_file)
    students.sync()


if __name__ == "__main__":
    main()
