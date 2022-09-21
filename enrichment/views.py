from collections import defaultdict
from datetime import date, timedelta
from functools import cache, cached_property
import json
from typing import Any, DefaultDict, Dict, List, Optional, Set, Tuple
import urllib.parse

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import TemplateView
from django.views.decorators.http import require_http_methods
from django.core.exceptions import SuspiciousOperation
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q
from pydantic import BaseModel, ValidationError, validator

import accounts.models
from blackbaud.models import Student, Teacher
from blackbaud.advising import get_advisees
from enrichment.models import Slot, Option, Signup
from enrichment.slots import GridGenerator, SlotID


class AssignAllPermissionRequired(PermissionRequiredMixin):
    permission_required = ["enrichment.assign_all_advisees"]


class Index(LoginRequiredMixin, TemplateView):
    template_name = "enrichment/index.html"


class AssignView(LoginRequiredMixin, TemplateView):
    """Default assignment view, which is for the user's advisees"""

    template_name = "enrichment/grid_standard.html"

    def get_title(self) -> str:
        return "My Advisees"

    @property
    def user(self) -> accounts.models.User:
        user = self.request.user
        if user.is_anonymous:
            raise ValueError("How did I get an anonymous user")

        assert isinstance(user, accounts.models.User)
        return user

    def get_students(self) -> List[Student]:
        teachers: Set[Teacher] = set(
            Teacher.objects.filter(active=True, email=self.user.email)
        )

        return sorted(
            {p.student for p in get_advisees(teachers)},
            key=lambda student: (
                student.family_name,
                student.nickname,
                student.given_name,
            ),
        )

    @cache
    def get_slots(self) -> List[Slot]:
        base_date = self.get_base_date()

        return sorted(
            Slot.objects.filter(
                date__gte=base_date, date__lt=(base_date + timedelta(days=7))
            ),
            key=lambda slot: slot.date,
        )

    def get_base_date(self) -> date:
        if val := self.request.GET.get("date"):
            try:
                return _parse_date(val)
            except ValueError as exc:
                raise SuspiciousOperation from exc

        return get_monday()

    def get_generator(self) -> GridGenerator:
        return GridGenerator(self.user, self.get_slots(), self.get_students())

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        base_date = self.get_base_date()
        today = get_monday()

        jump_slots = Slot.objects.all()
        jump_slots = jump_slots.filter(date__gte=today)
        jump_slots = jump_slots.filter(date__lt=(today + timedelta(days=180)))
        jump_slot_dates = {row["date"] for row in jump_slots.values("date")}
        jump_dates = sorted({get_monday(d) for d in jump_slot_dates})

        current_url = self.request.get_full_path()

        def get_week_jump(d: date) -> Tuple[str, date]:
            url_parts = urllib.parse.urlparse(current_url)
            query_params = dict(urllib.parse.parse_qsl(url_parts.query))
            query_params.update({"date": d.strftime("%Y-%m-%d")})
            encoded_query_params = urllib.parse.urlencode(query_params)
            new_url_parts = url_parts._replace(query=encoded_query_params)

            return new_url_parts.geturl(), d

        jumps = [get_week_jump(d) for d in jump_dates]

        context["week_of"] = base_date
        context["grid"] = self.get_generator()
        context["jump_weeks"] = jumps
        context["title"] = self.get_title()

        return context


class AssignAllView(AssignAllPermissionRequired, AssignView):
    """Assign all advisees"""

    def get_title(self) -> str:
        return "All Advisees"

    def get_students(self) -> List[Student]:
        all_students = {pair.student for pair in get_advisees()}
        return sorted(
            all_students,
            key=lambda obj: (obj.family_name, obj.nickname, obj.given_name),
        )


class AssignForAdvisorView(AssignAllPermissionRequired, AssignView):
    """Assign the advisees for a specific advisor"""

    def get_title(self) -> str:
        return f"Advisees for {self.teacher.full_name}"

    @cached_property
    def teacher(self) -> Teacher:
        return get_object_or_404(Teacher, pk=self.kwargs["teacher_id"])

    def get_students(self) -> List[Student]:
        students = sorted(
            {pair.student for pair in get_advisees([self.teacher])},
            key=lambda obj: (obj.family_name, obj.nickname, obj.given_name),
        )

        return students


class AssignUnassignedView(AssignAllView):
    """Assignment view for only unassigned advisees"""

    def get_title(self) -> str:
        return "Unassigned Advisees"

    def get_students(self) -> List[Student]:
        slots = set(self.get_slots())
        students = super().get_students()

        signups = Signup.objects.filter(
            slot__in=slots, student__in=students
        ).select_related("student", "slot")
        signups_by_student: DefaultDict[Student, Set[Slot]] = defaultdict(set)
        for signup in signups:
            signups_by_student[signup.student].add(signup.slot)

        def is_fully_assigned(student: Student) -> bool:
            assigned = signups_by_student[student]
            return assigned == slots
            return not (signups_by_student[student] - slots)

        return [obj for obj in students if not is_fully_assigned(obj)]


class AdviseeListView(AssignAllPermissionRequired, TemplateView):
    template_name = "enrichment/advisee_list.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        advisees = sorted(
            {p.student for p in get_advisees()},
            key=lambda student: (
                student.family_name,
                student.nickname,
                student.given_name,
            ),
        )

        context["advisees"] = advisees
        return context


class AdvisorListView(AssignAllPermissionRequired, TemplateView):
    template_name = "enrichment/advisor_list.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        advisors = sorted(
            {p.teacher for p in get_advisees()},
            key=lambda teacher: (
                teacher.family_name,
                teacher.given_name,
            ),
        )

        context["advisors"] = advisors
        return context


class AssignByStudentView(AssignAllView):
    """Assignment view for only a single student"""

    template_name = "enrichment/grid_flipped.html"

    def get_title(self) -> str:
        return self.student.display_name

    @cached_property
    def student(self) -> Student:
        return get_object_or_404(Student, pk=self.kwargs["student_id"])

    def get_students(self) -> List[Student]:
        return [self.student]

    @cache
    def get_slots(self) -> List[Slot]:
        date_from = self.get_base_date()
        date_to = date_from + timedelta(days=180)

        date_q = Q(date__gte=date_from, date__lte=date_to)

        slots = Slot.objects.filter(date_q).order_by("date")
        return list(slots)


def get_monday(d: Optional[date] = None):
    today = date.today()
    if d:
        today = d

    # Since Monday is 0 this logic works
    monday = today - timedelta(days=today.weekday())
    return monday


class AssignInput(BaseModel):
    slot_id: int
    student_id: int
    option_id: int | None
    admin_lock: bool = False

    # Todo: These validators are inefficient, they should use some sort
    # of computed property. Right now the table gets queried twice

    @validator("slot_id")
    def slot_must_exist(cls, v):
        if not Slot.objects.filter(pk=v).exists():
            raise ValueError("Slot does not exist")

        return v

    @validator("student_id")
    def student_must_exist(cls, v):
        if not Student.objects.filter(pk=v).exists():
            raise ValueError("Student does not exist")

        return v

    @validator("option_id")
    def option_must_exist(cls, v):
        if not v:
            return v

        if not Option.objects.filter(pk=v).exists():
            raise ValueError("Option does not exist")

        return v

    def get_student(self) -> Student:
        return Student.objects.get(pk=self.student_id)

    def get_slot(self) -> Slot:
        return Slot.objects.get(pk=self.slot_id)

    def get_option(self) -> Option | None:
        if not self.option_id:
            return None

        return Option.objects.get(pk=self.option_id)


@login_required
@require_http_methods(["POST"])
def assign(request: HttpRequest) -> JsonResponse:
    try:
        json_data = json.loads(request.body)
        data = AssignInput(**json_data)
    except ValidationError as exc:
        return JsonResponse(
            {
                "success": False,
                "code": "validation-failed",
                "errors": exc.errors(),
            }
        )
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "success": False,
                "code": "json-parse-failed",
            }
        )

    student = data.get_student()
    slot = data.get_slot()
    option = data.get_option()

    assert isinstance(request.user, accounts.models.User)
    generator = GridGenerator(request.user, [slot], [student])

    # One slot one student should have one row with one column
    assert len(generator.rows) == 1
    row = generator.rows[0]
    assert len(row.slots) == 1
    config = row.slots[0]

    if not config.editable:
        return JsonResponse(
            {
                "success": False,
                "code": "slot-not-editable",
            }
        )

    if not option:
        Signup.objects.filter(slot=slot, student=student).delete()
        return JsonResponse({"success": True})

    all_options = config.preferred_options + config.remaining_options
    all_option_ids = [int(obj.id) for obj in all_options]

    if not option.pk in all_option_ids:
        return JsonResponse(
            {
                "success": False,
                "code": "option-not-applicable",
            }
        )

    try:
        signup = Signup.objects.get(slot=slot, student=student)
    except Signup.DoesNotExist:
        signup = Signup(slot=slot, student=student)

    signup.admin_locked = data.admin_lock
    signup.option = option
    signup.save()

    return JsonResponse({"success": True})


def _parse_date(s: str) -> date:
    parts = s.split("-")
    if len(parts) != 3:
        raise ValueError("Date must be in form yyyy-mm-dd")

    year, month, day = map(int, parts)

    return date(year, month, day)
