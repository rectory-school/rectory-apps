"""Synchronization methods for Blackbaud"""

from datetime import datetime
import time
from typing import Callable, Dict, Iterable, List, Optional, TypeVar
import urllib.parse
from base64 import b64encode

from structlog import get_logger
from structlog.stdlib import BoundLogger

import requests

log: BoundLogger = get_logger(__name__)


from django.utils.translation import gettext as _
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from blackbaud import models

Model = TypeVar("Model", bound=models.SISModel)


class SyncNotReady(Exception):
    """The sync isn't ready to be run yet"""

    def __init__(self, next_run: datetime):
        self.next_run = next_run


class SyncNotEnabled(Exception):
    """The sync has not been enabled"""


class SyncNotConfigured(Exception):
    def __init__(self, param_name: str):
        self.param_name = param_name


class API:
    """Blackbaud API management endpoint"""

    def __init__(self):
        self._access_token_expiration: float = 0
        self._cached_access_token: str = ""

    @property
    def _access_token(self) -> str:
        """Get the cached access token or create a new one"""

        if self._access_token_expiration < time.monotonic():
            resp = self._get_access_token_request()
            resp.raise_for_status()

            data = resp.json()
            self._cached_access_token = data["access_token"]
            expiration_delay = data["expires_in"] * 0.75
            # For sanity, only hold the bearer token available for 75% of its actual time to avoid the edge case
            self._access_token_expiration = time.monotonic() + expiration_delay

        return self._cached_access_token

    @property
    def _token_url(self) -> str:
        if out := settings.BLACKBAUD_TOKEN_URL:
            return out

        raise SyncNotConfigured("BLACKBAUD_TOKEN_URL")

    @property
    def _api_base_url(self) -> str:
        if out := settings.BLACKBAUD_API_BASE:
            return out

        raise SyncNotConfigured("BLACKBAUD_API_BASE")

    @property
    def _oauth_key(self) -> str:
        if out := settings.BLACKBAUD_OAUTH_KEY:
            return out

        raise SyncNotConfigured("BLACKBAUD_OAUTH_KEY")

    @property
    def _oauth_secret(self) -> str:
        if out := settings.BLACKBAUD_OAUTH_SECRET:
            return out

        raise SyncNotConfigured("BLACKBAUD_OAUTH_SECRET")

    def _get_access_token_request(self):
        data = {
            "grant_type": "client_credentials",
            "scope": "https://purl.imsglobal.org/spec/or/v1p1/scope/roster-core.readonly",
        }

        to_encode = f"{self._oauth_key}:{self._oauth_secret}"
        encoded_key = b64encode(to_encode.encode("ascii")).decode("ascii")

        headers = {"Authorization": f"Basic {encoded_key}"}

        resp = requests.post(self._token_url, data=data, headers=headers)
        return resp

    def get(self, endpoint: str):
        headers = {
            "Authorization": f"Bearer {self._access_token}",
        }

        params = {"limit": 100, "offset": 0}

        records: List[Dict] = []
        expected_count: Optional[int] = None

        while expected_count is None or len(records) < expected_count:
            url = f"{self._api_base_url}{endpoint}?{urllib.parse.urlencode(params)}"
            log.debug("Getting URL", url=url)
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()
            json_data = resp.json()
            expected_count = int(resp.headers["x-total-count"])
            keys = json_data.keys()

            if len(keys) != 1:
                raise ValueError("Got multiple keys")

            key = set(keys).pop()
            data = json_data[key]
            records.extend(data)
            params["offset"] += params["limit"]

        out = {record["sourcedId"]: record for record in records}

        return out


def auto_sync(force=False):
    # This just ensures the singleton exists
    models.SyncConfig.get_solo()

    with transaction.atomic():
        config: models.SyncConfig = models.SyncConfig.objects.select_for_update().get()

        if not force:
            if not config.sync_enabled:
                raise SyncNotEnabled()

            if not config.ready_for_sync:
                raise SyncNotReady(config.next_sync)

        config.last_sync_attempt = timezone.now()
        config.sync_asap = False
        config.save()

        with transaction.atomic():
            _sync()


def _sync():
    log.info("Beginning Blackbaud sync")

    api = API()

    schools = _auto_sync(
        api,
        models.School,
        "/afe-rostr/ims/oneroster/v1p1/schools",
        _transform_schools,
    )

    courses = _auto_sync(
        api,
        models.Course,
        "/afe-rostr/ims/oneroster/v1p1/courses",
        _transform_course,
    )

    classes = _auto_sync(
        api,
        models.Class,
        "/afe-rostr/ims/oneroster/v1p1/classes",
        _get_transform_classes(schools, courses),
    )

    teachers = _auto_sync(
        api,
        models.Teacher,
        "/afe-rostr/ims/oneroster/v1p1/teachers",
        _get_transform_teachers(schools),
    )

    students = _auto_sync(
        api,
        models.Student,
        "/afe-rostr/ims/oneroster/v1p1/students",
        _get_transform_students(schools),
    )

    _sync_enrollments(api, schools, teachers, students, classes)

    log.info("Blackbaud sync finished")


def _auto_sync(
    api: API,
    model: Model,
    endpoint: str,
    transform: Callable[[Dict], Dict],
) -> Dict[str, Model]:
    """Perform an auto sync"""

    sis_data = api.get(endpoint)

    return _inner_sync(model, sis_data, transform)


def _inner_sync(
    model: Model,
    sis_data: Dict,
    transform: Callable[[Dict], Dict],
) -> Dict[str, Model]:
    """Perform an auto-sync using the transforms"""

    fields = model._meta.get_fields()
    many_to_many_fields = {
        field.attname  # type: ignore[union-attr]
        for field in fields
        if not field.auto_created and field.many_to_many
    }

    related_fields = {
        field.name  # type: ignore[union-attr]
        for field in fields
        if not field.auto_created and field.many_to_one
    }

    def get_desired_attrs(row: Dict):
        attrs = transform(row)
        if "active" not in attrs:
            attrs["active"] = row["status"] == "active"

        if "sis_id" not in attrs:
            attrs["sis_id"] = row["sourcedId"]

        return attrs

    objs: Iterable[Model] = (
        model.objects.all()
        .select_related(*related_fields)
        .prefetch_related(*many_to_many_fields)
    )
    objs_by_id = {obj.sis_id: obj for obj in objs}

    to_add = sis_data.keys() - objs_by_id.keys()
    to_remove = objs_by_id.keys() - sis_data.keys()
    matched = objs_by_id.keys() & sis_data.keys()

    for source_id in to_add:
        row = sis_data[source_id]

        desired_attrs = get_desired_attrs(row)

        desired_scalar_attrs = {
            k: v for k, v in desired_attrs.items() if k not in many_to_many_fields
        }

        desired_many_to_many_attrs = {
            k: v for k, v in desired_attrs.items() if k in many_to_many_fields
        }

        obj = model(**desired_scalar_attrs)  # type: ignore[operator]
        obj.save()
        objs_by_id[source_id] = obj

        # Now handle many to many
        for attr, desired_set in desired_many_to_many_attrs.items():
            getattr(obj, attr).set(desired_set)

    # Only soft delete
    for source_id in to_remove:
        obj = sis_data[source_id]
        if obj.active:
            obj.active = False
            obj.save()

    for source_id in matched:
        row = sis_data[source_id]
        obj = objs_by_id[source_id]

        desired_attrs = get_desired_attrs(row)

        desired_scalar_attrs = {
            k: v for k, v in desired_attrs.items() if k not in many_to_many_fields
        }

        desired_many_to_many_attrs = {
            k: v for k, v in desired_attrs.items() if k in many_to_many_fields
        }

        do_save = False
        for attr, desired_value in desired_scalar_attrs.items():
            if attr in many_to_many_fields:
                continue
            current_value = getattr(obj, attr)
            if current_value != desired_value:
                setattr(obj, attr, desired_value)
                do_save = True

        if do_save:
            obj.save()

        for attr, desired_value in desired_many_to_many_attrs.items():
            current_value = getattr(obj, attr).all()
            if set(current_value) != set(desired_value):
                getattr(obj, attr).set(desired_value)

    return objs_by_id


def _sync_enrollments(
    api: API,
    schools: Dict[str, models.School],
    teachers: Dict[str, models.Teacher],
    students: Dict[str, models.Student],
    classes: Dict[str, models.Class],
):
    data = api.get("/afe-rostr/ims/oneroster/v1p1/enrollments")

    student_data = {k: v for k, v in data.items() if v["role"] == "student"}
    teacher_data = {k: v for k, v in data.items() if v["role"] == "teacher"}

    _inner_sync(  # type: ignore[type-var]
        models.TeacherEnrollment,
        teacher_data,
        _get_transform_teacher_enrollments(
            teachers,
            classes,
            schools,
        ),
    )

    _inner_sync(  # type: ignore[type-var]
        models.StudentEnrollment,
        student_data,
        _get_transform_student_enrollments(
            students,
            classes,
            schools,
        ),
    )


def _transform_schools(row: Dict):
    return {
        "name": row["name"],
    }


def _transform_course(row: Dict):
    return {
        "title": row["title"],
    }


def _get_transform_teachers(schools: Dict[str, models.School]):
    def inner(row):
        return {
            "given_name": row["givenName"],
            "family_name": row["familyName"],
            "email": row["email"],
            "schools": [schools[org["sourcedId"]] for org in row["orgs"]],
        }

    return inner


def _get_transform_students(schools: Dict[str, models.School]):
    def inner(row):
        return {
            "given_name": row["givenName"],
            "family_name": row["familyName"],
            "email": row["email"],
            "grade": row["metadata"]["grade"],
            "schools": [schools[org["sourcedId"]] for org in row["orgs"]],
        }

    return inner


def _get_transform_classes(
    schools: Dict[str, models.School],
    courses: Dict[str, models.Course],
):
    def inner(row: Dict):
        return {
            "title": row["title"],
            "school": schools[row["school"]["sourcedId"]],
            "course": courses[row["course"]["sourcedId"]],
        }

    return inner


def _get_transform_student_enrollments(
    students: Dict[str, models.Student],
    classes: Dict[str, models.Class],
    schools: Dict[str, models.School],
):
    def inner(row):
        return {
            "student": students[row["user"]["sourcedId"]],
            "section": classes[row["class"]["sourcedId"]],
            "school": schools[row["school"]["sourcedId"]],
            "begin_date": row["beginDate"],
            "end_date": row["endDate"],
        }

    return inner


def _get_transform_teacher_enrollments(
    teachers: Dict[str, models.Teacher],
    classes: Dict[str, models.Class],
    schools: Dict[str, models.School],
):
    def inner(row):
        return {
            "teacher": teachers[row["user"]["sourcedId"]],
            "section": classes[row["class"]["sourcedId"]],
            "school": schools[row["school"]["sourcedId"]],
            "begin_date": row["beginDate"],
            "end_date": row["endDate"],
        }

    return inner


def encode_token(key: str, secret: str) -> str:
    to_encode = f"{key}:{secret}"
    encoded = b64encode(to_encode.encode("ascii")).decode("ascii")
    return encoded
