from datetime import date, timedelta
from functools import cached_property
import json
from typing import Any, Dict, List, Optional, Set, Tuple

from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.views.decorators.http import require_http_methods
from django.http import HttpRequest, JsonResponse

from pydantic import BaseModel, ValidationError, validator

from blackbaud.models import Student, Teacher
from blackbaud.advising import get_advisees
from enrichment.models import Slot, Option, Signup
from enrichment.slots import slot_assignment_data, SlotData


class Index(LoginRequiredMixin, TemplateView):
    template_name = "enrichment/index.html"


class AdvisorView(LoginRequiredMixin, TemplateView):
    template_name = "enrichment/advisor.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assert isinstance(user, AbstractBaseUser)

        email: str = user.email  # type: ignore[assignment,union-attr]

        if not email:
            return context

        teachers: Set[Teacher] = set(Teacher.objects.filter(active=True, email=email))
        monday = current_monday()
        next_monday = monday + timedelta(days=7)
        slots = sorted(
            Slot.objects.filter(date__gte=monday, date__lt=next_monday),
            key=lambda slot: slot.date,
        )

        advisees = sorted(
            {p.student for p in get_advisees(teachers)},
            key=lambda student: (
                student.family_name,
                student.nickname,
                student.given_name,
            ),
        )

        calc = slot_assignment_data(slots, advisees, user)

        grid: List[Tuple[Student, List[SlotData]]] = []

        for advisee in advisees:
            row: Tuple[Student, List[SlotData]] = (advisee, [])

            for slot in slots:
                key = (slot, advisee)
                row[1].append(calc[key])

            grid.append(row)

        options_by_pk: Dict[int, Dict] = {}
        for slot_data in calc.values():
            for option in slot_data.all_options:
                options_by_pk[option.pk] = {
                    "id": option.pk,
                    "location": option.location,
                    "description": option.description,
                    "teacher": option.teacher.formal_name,
                    "display": str(option),
                }

        context["week_of"] = current_monday()
        context["slots"] = slots
        context["advisees"] = advisees
        context["grid"] = grid
        context["all_options"] = options_by_pk
        return context


def current_monday(d: Optional[date] = None):
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

    # We will always have a real user here since login is required
    assert isinstance(request.user, AbstractBaseUser)
    calc = slot_assignment_data([slot], [student], request.user)
    calc_result = calc[(slot, student)]

    if not calc_result.editable:
        return JsonResponse(
            {
                "success": False,
                "code": "slot-not-editable",
            }
        )

    if not option:
        Signup.objects.filter(slot=slot, student=student).delete()
        return JsonResponse({"success": True})

    if not option in calc_result.all_options:
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
