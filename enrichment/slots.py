"""Slot calculation options"""

from datetime import date, datetime
from functools import cached_property
from types import MappingProxyType
from typing import (
    Dict,
    List,
    NamedTuple,
    NewType,
    Optional,
    Set,
    Tuple,
    FrozenSet,
)

from frozendict.core import frozendict

from django.db.models import QuerySet, Q
from django.utils import timezone

from accounts.models import User
from blackbaud.models import Student, Teacher
from blackbaud.students import teachers_for_students
from enrichment.models import Slot, Option, Signup

SlotID = NewType("SlotID", int)
StudentID = NewType("StudentID", int)
TeacherID = NewType("TeacherID", int)
OptionID = NewType("OptionID", int)


class GridTeacher(NamedTuple):
    id: TeacherID
    honorific: str
    last_name: str
    first_name: str
    email: str

    @property
    def jsonable(self) -> dict:
        return {f: getattr(self, f) for f in self._fields}

    @property
    def formal_name(self) -> str:
        if self.honorific:
            return f"{self.honorific}. {self.last_name}"

        return self.name

    @property
    def name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def sort_key(self) -> tuple:
        return self.last_name, self.first_name


class GridSlot(NamedTuple):
    id: SlotID
    date: date
    description: str
    editable_until: datetime


class GridOption(NamedTuple):
    """An option in the grid *for a given slot*"""

    id: OptionID
    teacher: GridTeacher
    location: str
    description: str
    start_date: date
    end_date: Optional[date]
    admin_only: bool
    exclude_from: FrozenSet[GridSlot]
    only_available_on: FrozenSet[GridSlot]
    location_overrides: MappingProxyType[GridSlot, str]

    def location_on_slot(self, slot: GridSlot) -> str:
        if slot in self.location_overrides:
            return self.location_overrides[slot]

        return self.location

    def is_available_for_slot(self, slot: GridSlot) -> bool:
        if slot in self.exclude_from:
            return False

        if self.only_available_on and not slot in self.only_available_on:
            return False

        if slot.date < self.start_date:
            return False

        if self.end_date and self.end_date < slot.date:
            return False

        return True

    @property
    def display(self) -> str:
        if self.description:
            return f"{self.teacher.name}: {self.description}"

        return self.teacher.name

    @property
    def jsonable(self) -> dict:
        out: dict = {}

        for field in self._fields:
            val = getattr(self, field)
            if isinstance(val, (set, frozenset)):
                val = list(val)

            if isinstance(val, frozendict):
                val = dict(val)

            out[field] = val

        out["teacher"] = self.teacher.jsonable
        out["display"] = self.display
        return out

    @property
    def sort_key(self) -> tuple:
        return self.teacher.sort_key


class GridStudent(NamedTuple):
    id: StudentID
    last_name: str
    first_name: str
    nickname: str

    @property
    def name(self) -> str:
        if self.nickname:
            return f"{self.nickname} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    @property
    def sort_key(self) -> tuple:
        if self.nickname:
            return self.last_name, self.nickname
        return self.last_name, self.first_name


class CurrentSelection(NamedTuple):
    slot: GridSlot
    current_option: GridOption
    admin_locked: bool

    @property
    def location(self) -> str:
        return self.current_option.location_on_slot(self.slot)

    @property
    def display(self) -> str:
        if self.current_option.description:
            return f"{self.current_option.description} with {self.current_option.teacher.formal_name} in {self.location}"

        return f"{self.current_option.teacher.formal_name} in {self.location}"


class GridRowSlot(NamedTuple):
    student: GridStudent
    slot: GridSlot
    currently_selected: Optional[CurrentSelection]
    preferred_options: List[GridOption]
    remaining_options: List[GridOption]
    editable: bool

    @property
    def preferred_option_ids(self) -> List[int]:
        return [opt.id for opt in self.preferred_options]

    @property
    def remaining_option_ids(self) -> List[int]:
        return [opt.id for opt in self.remaining_options]

    @property
    def current_option_id(self) -> Optional[int]:
        if self.currently_selected:
            return self.currently_selected.current_option.id

        return None

    @property
    def admin_locked(self) -> bool:
        if not self.currently_selected:
            return False

        return self.currently_selected.admin_locked


class GridRow(NamedTuple):
    student: GridStudent
    slots: List[GridRowSlot]


class PivotedGridRow(NamedTuple):
    slot: GridSlot
    students: List[GridRowSlot]


class GridSignup(NamedTuple):
    """Full signup information"""

    slot: GridSlot
    option: GridOption
    student: GridStudent
    admin_locked: bool
    assignment_is_valid: bool


class _RawSignup(NamedTuple):
    slot_id: SlotID
    student_id: StudentID
    option_id: OptionID
    admin_locked: bool


class GridGenerator:
    def __init__(
        self,
        user: User | None,
        slots: List[Slot],
        students: List[Student],
    ):
        self._user = user
        self._slots = slots
        self._students = students

    @cached_property
    def _can_set_admin_locked(self) -> bool:
        if not self._user:
            return False
        return self._user.has_perm("enrichment.set_admin_locked")

    @cached_property
    def _edit_past_lockout(self) -> bool:
        if not self._user:
            return False
        return self._user.has_perm("enrichment.edit_past_lockout")

    @cached_property
    def _alow_admin_only(self) -> bool:
        if not self._user:
            return False
        return self._user.has_perm("enrichment.use_admin_only_options")

    @cached_property
    def slots(self) -> List[GridSlot]:
        slots = (_slot_to_grid(obj) for obj in self._slots)
        return sorted(slots, key=lambda gs: (gs.date, gs.id))

    @cached_property
    def slots_by_id(self) -> Dict[SlotID, GridSlot]:
        return {slot.id: slot for slot in self.slots}

    @cached_property
    def students(self) -> List[GridStudent]:
        def transform(obj: Student) -> GridStudent:
            return GridStudent(
                id=StudentID(obj.pk),
                last_name=obj.family_name,
                first_name=obj.given_name,
                nickname=obj.nickname,
            )

        students = (transform(obj) for obj in self._students)
        return sorted(
            students, key=lambda obj: (obj.last_name, obj.nickname, obj.first_name)
        )

    @cached_property
    def students_by_id(self) -> Dict[StudentID, GridStudent]:
        return {obj.id: obj for obj in self.students}

    @cached_property
    def _raw_signups(self) -> set[_RawSignup]:
        """Raw signups to remove a recursion issue with options calling signups"""
        slot_ids = self.slots_by_id.keys()
        student_ids = self.students_by_id.keys()

        rows = Signup.objects.filter(
            slot_id__in=slot_ids, student_id__in=student_ids
        ).values("slot_id", "option_id", "student_id", "admin_locked")

        return {
            _RawSignup(
                SlotID(row["slot_id"]),
                StudentID(row["student_id"]),
                OptionID(row["option_id"]),
                row["admin_locked"],
            )
            for row in rows
        }

    @cached_property
    def signups(self) -> Set[GridSignup]:
        def get(row: _RawSignup) -> GridSignup:
            slot = self.slots_by_id[row.slot_id]
            option = self.options_by_id[row.option_id]
            student = self.students_by_id[row.student_id]
            admin_locked = row.admin_locked

            return GridSignup(
                slot=slot,
                option=option,
                student=student,
                admin_locked=admin_locked,
                assignment_is_valid=option in self.options_by_slot[slot],
            )

        return {get(row) for row in self._raw_signups}

    @cached_property
    def all_options(self) -> Set[GridOption]:
        out: Set[GridOption] = set()

        used_ids = {signup.option_id for signup in self._raw_signups}
        relevant_option_query = Q(pk__in=used_ids)

        if self.slots:
            low_date = min(slot.date for slot in self.slots)
            high_date = max(slot.date for slot in self.slots)

            low_date_query = Q(start_date__lte=high_date)
            high_date_query = Q(end_date__isnull=True) | Q(end_date__gte=low_date)
            date_query = low_date_query & high_date_query
            relevant_option_query |= date_query

        # Our query should now get us and option that was in used and any option
        # that might be relevant given our slot date ranges
        options: QuerySet[Option] = (
            Option.objects.filter(relevant_option_query)
            .prefetch_related(
                "only_available_on", "not_available_on", "location_overrides"
            )
            .select_related("teacher")
        )

        for obj in options:
            id = OptionID(obj.pk)
            not_available_on_ids: Set[SlotID] = set()
            only_available_on_ids: Set[SlotID] = set()
            location_overrides_by_id: Dict[SlotID, str] = {}

            for db_slot in obj.not_available_on.all():
                not_available_on_ids.add(SlotID(db_slot.pk))

            for db_slot in obj.only_available_on.all():
                only_available_on_ids.add(SlotID(db_slot.pk))

            for db_override in obj.location_overrides.all():
                location_overrides_by_id[
                    SlotID(db_override.slot_id)
                ] = db_override.location

            teacher = _teacher_to_grid(obj.teacher)
            exclude_from = {
                slot
                for slot_id, slot in self.slots_by_id.items()
                if slot_id in not_available_on_ids
            }
            only_available_on = {
                slot
                for slot_id, slot in self.slots_by_id.items()
                if slot_id in only_available_on_ids
            }
            location_overrides = {
                self.slots_by_id[slot_id]: location
                for (slot_id, location) in location_overrides_by_id.items()
            }

            option = GridOption(
                id=id,
                teacher=teacher,
                location=obj.location,
                description=obj.description,
                start_date=obj.start_date,
                end_date=obj.end_date,
                admin_only=obj.admin_only,
                exclude_from=frozenset(exclude_from),
                only_available_on=frozenset(only_available_on),
                location_overrides=frozendict(location_overrides),  # type: ignore
            )
            out.add(option)

        return out

    @cached_property
    def options_by_slot(self) -> Dict[GridSlot, Set[GridOption]]:
        out: Dict[GridSlot, set[GridOption]] = {}

        for slot in self.slots:
            out[slot] = set()

            for option in self.all_options:
                if option.is_available_for_slot(slot):
                    out[slot].add(option)

        return out

    @cached_property
    def options_by_id(self) -> Dict[OptionID, GridOption]:
        return {obj.id: obj for obj in self.all_options}

    @property
    def options_for_json(self) -> Dict[OptionID, dict]:
        return {obj.id: obj.jsonable for obj in self.all_options}

    @cached_property
    def grid_row_slots(self) -> Dict[Tuple[GridStudent, GridSlot], GridRowSlot]:
        out: Dict[Tuple[GridStudent, GridSlot], GridRowSlot] = {}

        organized_signups = {(row.slot.id, row.student.id): row for row in self.signups}

        def get_grid_row(student: GridStudent, slot: GridSlot) -> GridRowSlot:
            current_signup_data = organized_signups.get((slot.id, student.id))
            current_signup: Optional[CurrentSelection] = None
            if current_signup_data:
                current_signup = CurrentSelection(
                    slot,
                    self.options_by_id[current_signup_data.option.id],
                    current_signup_data.admin_locked,
                )

            def is_editable() -> bool:
                if slot.editable_until < timezone.now() and not self._edit_past_lockout:
                    return False

                if (
                    current_signup_data
                    and current_signup_data.admin_locked
                    and not self._can_set_admin_locked
                ):
                    return False

                # If a student is set to an admin only option and the
                # editor can't use admin only options, that's a lock
                if (
                    current_signup
                    and current_signup.current_option.admin_only
                    and not self._alow_admin_only
                ):
                    return False

                return True

            all_options = self.options_by_slot[slot]
            if not self._alow_admin_only:
                all_options -= {opt for opt in all_options if opt.admin_only}

            preferred_teachers = self.student_teacher_associations[(student, slot.date)]

            preferred_options = {
                opt for opt in all_options if opt.teacher in preferred_teachers
            }
            remaining_options = all_options - preferred_options

            return GridRowSlot(
                student=student,
                slot=slot,
                currently_selected=current_signup,
                preferred_options=sorted(
                    preferred_options,
                    key=lambda opt: (opt.teacher.last_name, opt.teacher.first_name),
                ),
                remaining_options=sorted(
                    remaining_options,
                    key=lambda opt: (opt.teacher.last_name, opt.teacher.first_name),
                ),
                editable=is_editable(),
            )

        for student in self.students:
            for slot in self.slots:
                key = (student, slot)
                grid_row = get_grid_row(student, slot)
                out[key] = grid_row

        return out

    @cached_property
    def rows(self) -> List[GridRow]:
        """Get the grid rows"""

        out: List[GridRow] = []

        for student in self.students:
            grid_rows = [self.grid_row_slots[(student, slot)] for slot in self.slots]
            out.append(GridRow(student=student, slots=grid_rows))

        return out

    @cached_property
    def pivoted_rows(self) -> List[PivotedGridRow]:
        """The pivoted rows, where each row is a date"""

        out: list[PivotedGridRow] = []

        for slot in self.slots:
            grid_rows = [
                self.grid_row_slots[(student, slot)] for student in self.students
            ]
            out.append(PivotedGridRow(slot=slot, students=grid_rows))

        return out

    @cached_property
    def dates(self) -> Set[date]:
        return {slot.date for slot in self.slots}

    @cached_property
    def student_teacher_associations(
        self,
    ) -> Dict[Tuple[GridStudent, date], Set[GridTeacher]]:
        db_data = teachers_for_students(self._students, dates=self.dates)

        out: Dict[Tuple[GridStudent, date], Set[GridTeacher]] = {}

        for (db_student, date), db_teachers in db_data.items():
            student = self.students_by_id[StudentID(db_student.pk)]
            out[(student, date)] = {
                _teacher_to_grid(db_teacher) for db_teacher in db_teachers
            }

        return out


def _slot_to_grid(obj: Slot) -> GridSlot:
    return GridSlot(
        id=SlotID(obj.pk),
        date=obj.date,
        description=obj.title,
        editable_until=obj.editable_until,
    )


def _teacher_to_grid(obj: Teacher) -> GridTeacher:
    return GridTeacher(
        id=TeacherID(obj.pk),
        last_name=obj.family_name,
        first_name=obj.given_name,
        honorific=obj.honorific,
        email=obj.email,
    )
