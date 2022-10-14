from ast import Add
from collections import defaultdict
from datetime import date, timedelta

from typing import Any, DefaultDict, Iterable, NamedTuple, Iterable, Optional

from black import out

from enrichment.models import (
    Slot,
    Signup,
    EmailConfig,
    RelatedAddress as DefaultAddress,
)
from enrichment.slots import (
    CurrentSelection,
    GridGenerator,
    GridOption,
    GridSignup,
    GridSlot,
    GridStudent,
    GridTeacher,
    SlotID,
    StudentID,
)
from stored_mail.models import OutgoingMessage, RelatedAddress
from blackbaud.advising import get_advisees_by_advisors, get_advisees
from blackbaud.models import Student, Teacher
from django.template.loader import render_to_string, TemplateDoesNotExist
from django.utils import timezone
from django.conf import settings

BASE_URL: str = settings.EMAIL_BASE_URL

_SignupIDs = set[tuple[SlotID, StudentID]]


class AddressPair(NamedTuple):
    name: str
    address: str


class OutgoingEmail(NamedTuple):
    cfg: EmailConfig
    template_name: str
    context: dict[str, Any]
    subject: str
    to_addresses: set[AddressPair] = set()
    cc_addresses: set[AddressPair] = set()
    bcc_addresses: set[AddressPair] = set()
    reply_to_addresses: set[AddressPair] = set()

    @property
    def message_text(self) -> str:
        full_template_name = f"enrichment/email/{self.template_name}.txt"
        return render_to_string(full_template_name, self.context)

    @property
    def message_html(self) -> str | None:
        full_template_name = f"enrichment/email/{self.template_name}.html"
        try:
            return render_to_string(full_template_name, self.context)
        except TemplateDoesNotExist:
            return None

    def create_outgoing_message(self) -> OutgoingMessage:
        """Create and return the outgoing message. This function
        count not be implemented as returning an unsaved object
        since the to, cc, bcc, and reply-to objects are foreign keys"""

        outgoing_message = OutgoingMessage()
        outgoing_message.from_name = self.cfg.from_name
        outgoing_message.from_address = self.cfg.from_address
        outgoing_message.subject = self.subject
        outgoing_message.text = self.message_text
        outgoing_message.html = self.message_html or ""
        outgoing_message.discard_after = timezone.now() + timedelta(days=1)
        outgoing_message.save()

        # Get the base addresses from the passed in variables
        pair_types = {
            "to": set(self.to_addresses),
            "cc": set(self.cc_addresses),
            "bcc": set(self.bcc_addresses),
            "reply-to": set(self.reply_to_addresses),
        }

        # Add on the default addresses
        for default_address in self.cfg.addresses.all():
            assert isinstance(default_address, DefaultAddress)

            pair_types[default_address.field].add(
                AddressPair(
                    name=default_address.name,
                    address=default_address.address,
                )
            )

        for field, address_pairs in pair_types.items():
            for pair in address_pairs:
                related_address = RelatedAddress()
                related_address.message = outgoing_message
                related_address.field = field
                related_address.name = pair.name
                related_address.address = pair.address
                related_address.save()
                del related_address

        return outgoing_message


def unassigned_admin(cfg: EmailConfig, slots: set[Slot]) -> Iterable[OutgoingEmail]:
    """Generate report for unassigned advisees to admins"""

    advisees_by_advisor = get_advisees_by_advisors()

    advisors_by_advisees: dict[Student, set[Teacher]] = {}
    all_students: set[Student] = set()

    for advisor, advisees in advisees_by_advisor.items():
        for student in advisees:
            if not student in advisors_by_advisees:
                advisors_by_advisees[student] = set()

            advisors_by_advisees[student].add(advisor)
            all_students.add(student)

    all_signups = {
        (SlotID(row["slot_id"]), StudentID(row["student_id"]))
        for row in Signup.objects.filter(slot__in=slots).values("slot_id", "student_id")
    }

    unassigned_by_slot: dict[Slot, set[Student]] = {}
    unassigned_students: set[Student] = set()

    # Calculate all unassigned students by slot
    for slot in slots:
        unassigned_by_slot[slot] = set()
        slot_id = SlotID(slot.pk)

        for student in all_students:
            student_id = StudentID(student.pk)
            key = (slot_id, student_id)

            if key not in all_signups:
                unassigned_by_slot[slot].add(student)
                unassigned_students.add(student)

    organized: list[tuple[Slot, list[tuple[Teacher, list[Student]]]]] = []

    # Organize into slot/advisor
    for slot in sorted(slots, key=lambda slot: slot.date):
        organized_slot: list[tuple[Teacher, list[Student]]] = []

        teachers = sorted(
            advisees_by_advisor.keys(),
            key=lambda teacher: (teacher.family_name, teacher.given_name),
        )

        for teacher in teachers:
            advisees = advisees_by_advisor[teacher]
            unassigned_advisees = sorted(
                unassigned_by_slot[slot] & advisees,
                key=lambda student: student.sort_key,
            )

            if unassigned_advisees:
                organized_slot.append((teacher, unassigned_advisees))

        organized.append((slot, organized_slot))

    context = {
        "count": len(unassigned_students),
        "base_url": BASE_URL,
        "slots": organized,
    }

    yield OutgoingEmail(
        cfg=cfg,
        template_name="unassigned_admin",
        context=context,
        subject=f"Unassigned advisee report: {len(unassigned_students)} total",
    )


def unassigned_advisor(cfg: EmailConfig, slots: set[Slot]) -> Iterable[OutgoingEmail]:
    """Generate reports for unassigned advisees to advisors"""

    data = get_advisees_by_advisors()
    all_students: set[Student] = set()
    for students in data.values():
        all_students.update(students)

    all_signups = {
        (SlotID(row["slot_id"]), StudentID(row["student_id"]))
        for row in Signup.objects.filter(slot__in=slots).values("slot_id", "student_id")
    }

    for advisor, advisees in data.items():
        if email := _unassigned_for_advisor(cfg, advisor, advisees, slots, all_signups):
            yield email


def _unassigned_for_advisor(
    cfg: EmailConfig,
    advisor: Teacher,
    advisees: set[Student],
    slots: set[Slot],
    all_signups: _SignupIDs,
) -> OutgoingEmail | None:

    unassigned_students: set[Student] = set()
    context_dict: DefaultDict[Slot, set[Student]] = defaultdict(set)

    for slot in slots:
        slot_id = SlotID(slot.pk)
        for student in advisees:
            student_id = StudentID(student.pk)
            key = (slot_id, student_id)

            if key not in all_signups:
                context_dict[slot].add(student)
                unassigned_students.add(student)

    if not context_dict:
        return None

    context_list = [
        (
            slot,
            sorted(students, key=lambda s: (s.family_name, s.nickname, s.given_name)),
        )
        for (slot, students) in context_dict.items()
    ]

    context = {
        "advisor": advisor,
        "deadline": min((slot.editable_until for slot in slots)) - timedelta(hours=1),
        "count": len(unassigned_students),
        "base_url": BASE_URL,
        "slots": context_list,
    }

    return OutgoingEmail(
        cfg=cfg,
        template_name="unassigned_advisor",
        context=context,
        subject="You have unassigned advisees",
        to_addresses={AddressPair(advisor.full_name, advisor.email)},
    )


def all_signups(cfg: EmailConfig, slots: set[Slot]) -> Iterable[OutgoingEmail]:
    students_by_id: dict[int, Student] = {
        pair.student.pk: pair.student for pair in get_advisees()
    }

    grid = GridGenerator(
        None,
        sorted(slots, key=lambda obj: obj.date),
        sorted(students_by_id.values(), key=lambda obj: obj.pk),
    )

    by_slot_option: defaultdict[
        tuple[GridSlot, GridOption], set[GridSignup]
    ] = defaultdict(set)

    for signup in grid.signups:
        by_slot_option[(signup.slot, signup.option)].add(signup)

    organized: list[tuple[GridSlot, list[tuple[GridOption, list[GridStudent]]]]] = []

    for slot in sorted(grid.slots, key=lambda obj: obj.date):
        organized_options: list[tuple[GridOption, list[GridStudent]]] = []

        for option in sorted(grid.options_by_slot[slot], key=lambda obj: obj.sort_key):
            signups = by_slot_option[(slot, option)]
            students = sorted(
                (obj.student for obj in signups), key=lambda obj: obj.sort_key
            )

            organized_options.append((option, students))

        organized.append((slot, organized_options))

    context = {"slots": organized}

    yield OutgoingEmail(
        cfg=cfg,
        template_name="all_signups",
        context=context,
        subject="Enrichment signups",
    )


def advisee_signups(cfg: EmailConfig, slots: set[Slot]) -> Iterable[OutgoingEmail]:
    """Personalized emails to every advisee"""

    ordered_slots = sorted(slots, key=lambda obj: obj.date)
    advisees = set(pair.student for pair in get_advisees())

    grid = GridGenerator(None, ordered_slots, list(advisees))

    dates = sorted({obj.date for obj in slots})
    subject_dates = comma_format_list([d.strftime("%A, %B %d") for d in dates])
    subject = f"Enrichment assignment for {subject_dates}"

    for advisee in advisees:
        organized: list[tuple[GridSlot, Optional[GridOption]]] = []
        grid_student = grid.students_by_id[StudentID(advisee.pk)]

        for slot in ordered_slots:
            grid_slot = grid.slots_by_id[SlotID(slot.pk)]
            key = (grid_student, grid_slot)
            signup = grid.grid_row_slots[key]
            current_option: GridOption | None = None

            if signup.currently_selected:
                current_option = signup.currently_selected.current_option

            organized.append((grid_slot, current_option))

        to_pair = AddressPair(advisee.display_name, advisee.email)

        yield OutgoingEmail(
            cfg=cfg,
            template_name="advisee_signups",
            context={"student": advisee, "slots": organized},
            subject=subject,
            to_addresses={to_pair},
        )


def advisor_signups(cfg: EmailConfig, slots: set[Slot]) -> Iterable[OutgoingEmail]:
    """Personalized emails to every advisor"""

    ordered_slots = sorted(slots, key=lambda obj: obj.date)
    advisees_by_advisors = get_advisees_by_advisors()
    students: set[Student] = set()

    for advisor_students in advisees_by_advisors.values():
        students.update(advisor_students)

    grid = GridGenerator(None, ordered_slots, list(students))

    for pair in get_advisees():
        advisor = pair.teacher
        if not advisor in advisees_by_advisors:
            advisees_by_advisors[advisor] = set()

        advisees_by_advisors[advisor].add(pair.student)

    dates = sorted({obj.date for obj in slots})
    subject_dates = comma_format_list([d.strftime("%A, %B %d") for d in dates])
    subject = f"Advisee enrichment assignment for {subject_dates}"

    for advisor, advisor_students in advisees_by_advisors.items():
        out: list[
            tuple[GridSlot, list[tuple[GridStudent, Optional[CurrentSelection]]]]
        ] = []

        for grid_slot in grid.slots:
            rows: list[tuple[GridStudent, Optional[CurrentSelection]]] = []
            for advisee in advisor_students:
                grid_student = grid.students_by_id[StudentID(advisee.pk)]
                key = (grid_student, grid_slot)
                signup = grid.grid_row_slots[key]
                rows.append((grid_student, signup.currently_selected))
            out.append((grid_slot, rows))

        to_pair = AddressPair(advisor.full_name, advisor.email)

        yield OutgoingEmail(
            cfg=cfg,
            template_name="advisor_signups",
            context={"slots": out, "advisor": advisor},
            subject=subject,
            to_addresses={to_pair},
        )


def facilitator_signups(cfg: EmailConfig, slots: set[Slot]) -> Iterable[OutgoingEmail]:
    """Personalized emails to every facilitator"""

    ordered_slots = sorted(slots, key=lambda obj: obj.date)
    students = {pair.student for pair in get_advisees()}
    grid = GridGenerator(None, ordered_slots, list(students))

    dates = sorted({obj.date for obj in slots})
    subject_dates = comma_format_list([d.strftime("%A, %B %d") for d in dates])
    subject = f"Students coming for enrichment on {subject_dates}"

    class ConcreteOption(NamedTuple):
        slot: GridSlot
        option: GridOption
        location: str

    signups_by_option: dict[ConcreteOption, set[GridStudent]] = {}

    # Because a teacher will still get an email even if there are no signups,
    # we are taking a walk through all the slots and options to make the scaffold
    # and not jumping straight to iterating the signups
    for slot in grid.slots:
        for option in grid.options_by_slot[slot]:
            concrete_option = ConcreteOption(
                slot=slot,
                option=option,
                location=option.location_on_slot(slot),
            )

            signups_by_option[concrete_option] = set()

    for signup in grid.signups:
        option = signup.option
        student = signup.student

        concrete_option = ConcreteOption(
            slot=slot,
            option=option,
            location=option.location_on_slot(slot),
        )

        signups_by_option[concrete_option].add(student)

    options_by_teacher: dict[GridTeacher, set[ConcreteOption]] = {}
    for concrete_option in signups_by_option:
        teacher = concrete_option.option.teacher

        if not teacher in options_by_teacher:
            options_by_teacher[teacher] = set()

        options_by_teacher[teacher].add(concrete_option)

    for teacher, options in options_by_teacher.items():
        organized: list[tuple[ConcreteOption, list[GridStudent]]] = []

        for concrete_option in sorted(options, key=lambda obj: obj.slot):
            organized.append(
                (
                    concrete_option,
                    sorted(
                        signups_by_option[concrete_option], key=lambda obj: obj.sort_key
                    ),
                )
            )
        context = {"teacher": teacher, "options": organized}

        yield OutgoingEmail(
            cfg=cfg,
            template_name="facilitator_signups",
            context=context,
            subject=subject,
            to_addresses={AddressPair(teacher.name, teacher.email)},
        )


def get_outgoing_messages(cfg: EmailConfig, date: date) -> Iterable[OutgoingEmail]:
    start_date = date + timedelta(days=cfg.start)
    end_date = date + timedelta(days=cfg.end)
    slots = set(Slot.objects.filter(date__gte=start_date, date__lte=end_date))

    callable_map = {
        "unassigned_advisor": unassigned_advisor,
        "unassigned_admin": unassigned_admin,
        "all_signups": all_signups,
        "advisee_signups": advisee_signups,
        "advisor_signups": advisor_signups,
        "facilitator_signups": facilitator_signups,
    }

    func = callable_map[cfg.report]
    yield from func(cfg, slots)


def execute_job(cfg: EmailConfig, date: date):
    outgoing = get_outgoing_messages(cfg, date)

    for msg in outgoing:
        msg.create_outgoing_message()

    cfg.last_sent = timezone.now()
    cfg.save()


def comma_format_list(elems: list[str]) -> str:
    if not elems:
        return ""

    if len(elems) == 1:
        return elems[0]

    if len(elems) == 2:
        return f"{elems[0]} and {elems[1]}"

    comma_parts = ", ".join(elems[0:-1])
    return f"{comma_parts}, and {elems[-1]}"
