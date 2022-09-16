"""Slot calculation options"""

from collections import defaultdict
from datetime import date
from typing import (
    DefaultDict,
    Dict,
    List,
    NamedTuple,
    Optional,
    Set,
    Tuple,
)

from django.db.models import QuerySet, Q
from django.contrib.auth.models import AbstractBaseUser
from django.utils import timezone

from blackbaud.models import Student, Teacher
from enrichment.models import Slot, Option, Signup


class SlotData(NamedTuple):
    slot: Slot
    student: Student
    current_option: Optional[Option]
    preferred_options: List[Option]
    remaining_options: List[Option]
    preferred_option_ids: List[int]
    remaining_option_ids: List[int]
    editable: bool

    @property
    def all_options(self) -> Set[Option]:
        return set(self.preferred_options) | set(self.remaining_options)


def slot_assignment_data(
    slots: List[Slot],
    students: List[Student],
    user: AbstractBaseUser,
) -> Dict[Tuple[Slot, Student], SlotData]:
    """Get all the data needed for the assignments"""

    options = options_for_slots(slots)
    signups = Signup.objects.filter(
        slot__in=slots, student__in=students
    ).select_related("slot", "student")

    keyed_signups: Dict[Tuple[Slot, Student], Signup] = {
        (signup.slot, signup.student): signup for signup in signups
    }

    # The permission system is installed, so we always have a has_perm attribute
    can_edit_past_time = user.has_perm("enrichment.edit_past_lockout")  # type: ignore[attr-defined]
    can_edit_when_admin_locked = user.has_perm("enrichment.ignore_admin_locked")  # type: ignore[attr-defined]
    admin_only_options_available = user.has_perm("enrichment.use_admin_only_options")  # type: ignore[attr-defined]

    return {
        (slot, student): _slot_data_for_slot_student(
            slot,
            options[slot],
            keyed_signups.get((slot, student)),
            set(),  # TODO: Add in preferred teachers
            student,
            can_edit_past_time,
            can_edit_when_admin_locked,
            admin_only_options_available,
        )
        for slot in slots
        for student in students
    }


def options_for_slots(slots: List[Slot]) -> Dict[Slot, Set[Option]]:
    """Calculate what slots are available for what options"""

    # We have to explicitly take a list because of how we do the low
    # and high date calculations

    low_date: date = min(slot.date for slot in slots)
    high_date: date = max(slot.date for slot in slots)

    options: QuerySet[Option] = (
        Option.objects.all()
        .prefetch_related("only_available_on", "not_available_on")
        .select_related("teacher")
    )

    # For an option to be relevant to any slot it has to
    # start before our highest slot date
    options = options.filter(start_date__lte=high_date)

    # For an option to be relevant it either has to have no end date,
    # or its end date has to be after our low date
    options = options.filter(Q(end_date__isnull=True) | Q(end_date__lte=low_date))

    # Pre-process only available on and not available on into sets
    not_available_on_by_option: DefaultDict[Option, Set[Slot]] = defaultdict(set)
    only_available_on_by_option: DefaultDict[Option, Set[Slot]] = defaultdict(set)

    for option in options:
        not_available_on_by_option[option] = set(option.not_available_on.all())
        only_available_on_by_option[option] = set(option.only_available_on.all())

    options_by_slot: Dict[Slot, Set[Option]] = {}

    for slot in slots:
        options_by_slot[slot] = set()

        for option in options:
            only_available_on = only_available_on_by_option[option]
            not_available_on = not_available_on_by_option[option]

            available = _option_available_for_slot(
                slot,
                option,
                only_available_on,
                not_available_on,
            )

            if available:
                options_by_slot[slot].add(option)

    return options_by_slot


def _option_available_for_slot(
    slot: Slot,
    option: Option,
    only_available_on: Set[Slot],
    not_available_on: Set[Slot],
) -> bool:
    """Check if a given option is available for a given slot"""

    # Only available on and not available on were pre-processed in a parent function
    # to make their lookups far more efficient from a set

    if option.start_date > slot.date:
        return False

    if option.end_date and option.end_date < slot.date:
        return False

    if only_available_on and not slot in only_available_on:
        return False

    if slot in not_available_on:
        return False

    return True


def _slot_data_for_slot_student(
    slot: Slot,
    options: Set[Option],
    current_signup: Optional[Signup],
    preferred_teachers: Set[Teacher],
    student: Student,
    allow_edit_past_time: bool,
    allow_edit_admin_locked: bool,
    allow_admin_only_options: bool,
) -> SlotData:
    """Get the slot data for an individual student thing"""

    non_editable = SlotData(
        slot=slot,
        student=student,
        current_option=current_signup and current_signup.option or None,
        preferred_options=[],
        remaining_options=[],
        preferred_option_ids=[],
        remaining_option_ids=[],
        editable=False,
    )

    # If we're past the edit time, no soup for you
    if timezone.now() > slot.editable_until and not allow_edit_past_time:
        return non_editable

    # If we're set to an admin only option and can't access admin only options,
    # we consider that the same as an admin lock
    if (
        current_signup
        and current_signup.option.admin_only
        and not allow_admin_only_options
    ):
        return non_editable

    if current_signup and current_signup.admin_locked and not allow_edit_admin_locked:
        return non_editable

    available_options = set(options)
    admin_only_options = {opt for opt in options if opt.admin_only}
    preferred_options = {opt for opt in options if opt.teacher in preferred_teachers}

    if not allow_admin_only_options:
        available_options -= admin_only_options

    remaining_options = available_options - preferred_options

    preferred_option_list = sorted(
        preferred_options,
        key=lambda opt: (opt.teacher.family_name, opt.teacher.given_name),
    )

    remaining_option_list = sorted(
        remaining_options,
        key=lambda opt: (opt.teacher.family_name, opt.teacher.given_name),
    )

    return SlotData(
        slot=slot,
        student=student,
        current_option=current_signup and current_signup.option or None,
        preferred_options=preferred_option_list,
        remaining_options=remaining_option_list,
        preferred_option_ids=[opt.pk for opt in preferred_option_list],
        remaining_option_ids=[opt.pk for opt in remaining_option_list],
        editable=True,
    )
