"""Base manager"""

from typing import List, Tuple, Dict, Iterable, Any, Union
from functools import wraps
import logging
import json

from requests import Request
from requests_futures.sessions import FuturesSession

log = logging.getLogger(__name__)


def run_once(f):
    """Runs a function (successfully) only once.

    The running can be reset by setting the `has_run` attribute to False
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            result = f(*args, **kwargs)
            wrapper.has_run = True
            return result
    wrapper.has_run = False
    return wrapper


class SyncManager:
    apps_url_key: str = None
    apps_key: str = None
    ks_key: str = None

    field_map: List[Tuple[str, str]] = None

    def __init__(self, session: FuturesSession, url_map: Dict[str, str], ks_filename: str = None):
        self.session = session
        self.url = url_map[self.apps_url_key]
        self.ks_filename = ks_filename
        self.apps_data = {}
        self.ks_data = {}

    @run_once
    def load_apps_data(self):
        url = self.url

        while url:
            log.info("Loading %s, %d records already loaded", url, len(self.apps_data))

            req = self.session.get(url).result().json()
            url = req["next"]

            for record in req["results"]:
                key = record[self.apps_key]
                self.apps_data[key] = record

        log.info("Finished loading from %s, got %d records", self.url, len(self.apps_data))

    @run_once
    def load_ks_data(self) -> Dict[str, dict]:
        with open(self.ks_filename) as f_in:
            data = json.load(f_in)
            self.ks_data = {record[self.ks_key]: record for record in data["records"]}

    def delete(self):
        self.load_apps_data()
        self.load_ks_data()

        to_delete = self.apps_data.keys() - self.ks_data.keys()

        waiting = []

        for key in to_delete:
            apps_record = self.apps_data[key]
            url = apps_record["url"]

            waiting.append(self.session.delete(url))
            del self.apps_data[key]

        for req in waiting:
            res = req.result()
            log.info("Deleted %s: %d", res.request.url, res.status_code)

    def create(self):
        self.load_apps_data()
        self.load_ks_data()

        to_create = self.ks_data.keys() - self.apps_data.keys()

        waiting = []

        for key in to_create:
            ks_record = self.ks_data[key]
            apps_record = self.translate(ks_record)
            waiting.append(self.session.post(self.url, data=apps_record))

        for req in waiting:
            res = req.result()
            data = res.json()

            if res.status_code == 201:
                log.info("Created %s: %d", data, res.status_code)

                key = data[self.apps_key]
                self.apps_data[key] = data  # Load back in for URLs and PK and such
                continue

            log.warning("Unexpected status code when creating %s with %s: %s", res.request, data, res.status_code)

    def update(self):
        self.load_apps_data()
        self.load_ks_data()

        update_candidates = self.ks_data.keys() & self.apps_data.keys()

        waiting = []

        for key in update_candidates:
            ks_translated = self.translate(self.ks_data[key])
            current_record = self.apps_data[key]

            if self.should_update():
                url = current_record["url"]

                waiting.append(self.session.post(url, data=self.translate(self.ks_data[key])))

    def translate(self, ks_record: Dict[str, Any]) -> Dict[str, Any]:
        """Translate a Keystone record into an apps record"""

        out = {}

        for apps_attr, ks_attr in self.field_map:
            out[apps_attr] = ks_record[ks_attr]

        return out

    def sync(self):
        self.load_ks_data()
        self.load_apps_data()

        self.create()
        self.update()
        self.delete()


def should_update(desired: Dict[str, Any], current: Dict[str, Any]) -> bool:
    """Determine if a record for a given key should be updated"""

    for attr_name, desired_value in desired.items():
        current_value = getattr(current, attr_name)

        if current_value != desired_value:
            return True

    return False
