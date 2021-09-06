#!/usr/bin/env python

"""SIS sync script"""

from dataclasses import dataclass
from typing import Iterable, Dict, List

from functools import cache
import argparse
import logging
import json

import requests

logging.basicConfig(filename='sync.log', level=logging.INFO)

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

    api_root = args.api_root
    username = args.username
    password = args.password

    loader = Loader(api_root, auth=(username, password))

    if student_file_name := args.student_file:
        with open(student_file_name) as f_in:
            data = json.load(f_in)
            sync_students(data, loader)


class Loader:
    def __init__(self, base_url, auth):
        self.auth = auth
        self.all_item_types = self._load_everything(base_url)

    def _load_everything(self, base_url) -> Dict[str, Iterable[Dict]]:
        """Load all API endpoints"""

        req = requests.get(base_url)

        out = {}

        for key, url in req.json().items():
            out[key] = load_all_records(url, self.auth)

        return out

    @cache
    def get_student_records(self) -> List[Dict]:
        out = []

        out.extend(self.all_item_types["students"])

        return out


def load_all_records(url, auth) -> Iterable[Dict]:
    count = 0
    while url:
        log.info("Loading %s, %d records already loaded", url, count)

        req = requests.get(url, auth=auth).json()
        url = req["next"]

        count += len(req["results"])
        yield from req["results"]


def sync_students(fm_data: Dict[str, Dict], loader: Loader):
    records = fm_data["records"]
    desired_students_by_id = {record["IDStudent"]: record for record in records}

    for apps_student in loader.get_student_records():
        student_id = apps_student["student_id"]
        url = apps_student["url"]

        if student_id not in desired_students_by_id:
            logging.warning("Removing student %s", student_id)
            requests.delete(url, auth=loader.auth).raise_for_status()
            continue


if __name__ == "__main__":
    main()
