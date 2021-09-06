#!/usr/bin/env python

"""SIS sync script"""

from typing import Iterable, Dict, List, Tuple, Generator

from functools import cache
import argparse
import logging
import json

from requests_futures.sessions import FuturesSession
from requests import Request


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
    parser.add_argument("--student-file")
    parser.add_argument("--teacher-file", default="ksTEACHERS.xml.json")
    parser.add_argument("--course-file", default="ksCOURSES.xml.json")
    parser.add_argument("--api-root", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)

    args = parser.parse_args()

    session = FuturesSession()
    session.auth = (args.username, args.password)

    url_map = session.get(args.api_root).result().json()

    if student_file_name := args.student_file:
        syncer = StudentSync(session, url_map, student_file_name)
        for cmd in syncer.get_deletions():

            print(cmd)


@cache
def load_all_records(session: FuturesSession, url: str) -> Iterable[Dict]:
    out = []
    while url:
        log.info("Loading %s, %d records already loaded", url, len(out))

        req = session.get(url).result().json()
        url = req["next"]

        out.extend(req["results"])

    log.info("Finished loading from %s, got %d records", url, len(out))
    return out


class SimpleSync:
    apps_url_name = None
    apps_key: str = None
    ks_key: str = None

    field_map: List[Tuple[str, str]] = None

    def __init__(self, session: FuturesSession, root_map: Dict[str, str], ks_filename: str):
        self.ks_filename = ks_filename
        self.session = session
        self.url = root_map[self.apps_url_name]

    @cache
    def _get_apps_data(self) -> Dict[str, Dict]:
        return {record[self.apps_key]: record for record in load_all_records(self.session, self.url)}

    @cache
    def _get_ks_data(self) -> Dict[str, dict]:
        with open(self.ks_filename) as f_in:
            data = json.load(f_in)
            return {record[self.ks_key]: record for record in data["records"]}

    def get_deletions(self) -> Iterable[Request]:
        apps_data = self._get_apps_data()
        ks_data = self._get_ks_data()

        to_delete = apps_data.keys() - ks_data.keys()

        for key in to_delete:
            apps_record = apps_data[key]
            url = apps_record["url"]
            yield Request(method="DELETE", url=url)


class StudentSync(SimpleSync):
    apps_url_name = "students"
    apps_key = "student_id"
    ks_key = "IDSTUDENT"
    field_map = [
        ('student_id', 'IDSTUDENT'),
        ('first_name', 'NameFirst'),
        ('last_name', 'NameLast'),
        ('nickname', 'NameNickname'),
        ('email', 'EMailSchool'),
        ('gender', 'Sex'),
    ]


if __name__ == "__main__":
    main()
