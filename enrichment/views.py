from datetime import date, timedelta
import json
from typing import Any, Dict, Optional, Set

from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.views.decorators.http import require_http_methods
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.db.models import Max

from pydantic import BaseModel, ValidationError, validator

import accounts.models
from blackbaud.models import Student, Teacher
from blackbaud.advising import get_advisees
from enrichment.models import Slot, Option, Signup
from enrichment.slots import GridGenerator, SlotID


class Index(LoginRequiredMixin, TemplateView):
    template_name = "enrichment/index.html"


class AdvisorView(LoginRequiredMixin, TemplateView):
    template_name = "enrichment/advisor.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        base_date = get_monday()
        date_str = self.request.GET.get("date")
        if date_str:
            try:
                base_date = _parse_date(date_str)
            except ValueError:
                # Just leave it as the original date
                pass

        user = self.request.user
        assert isinstance(user, AbstractBaseUser)

        email: str = user.email  # type: ignore[assignment,union-attr]

        if not email:
            return context

        teachers: Set[Teacher] = set(Teacher.objects.filter(active=True, email=email))

        slots = sorted(
            Slot.objects.filter(
                date__gte=base_date, date__lt=(base_date + timedelta(days=7))
            ),
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

        grid = GridGenerator(user, slots, advisees)

        jump_slot_dates = Slot.objects.filter(
            date__gte=date.today(), date__lt=date.today() + timedelta(days=180)
        ).values("date")
        jump_weeks = sorted({get_monday(row["date"]) for row in jump_slot_dates})

        context["week_of"] = base_date
        context["grid"] = grid
        context["next_week"] = base_date + timedelta(days=7)
        context["last_week"] = base_date - timedelta(days=7)
        context["jump_weeks"] = jump_weeks

        return context


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
