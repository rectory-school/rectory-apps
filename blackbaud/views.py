"""General SIS views"""

from typing import Any, DefaultDict, Dict, List
from collections import defaultdict
from django.views.generic import TemplateView
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin

from blackbaud.models import Teacher, Student

from blackbaud.advising import get_advisees


class Index(LoginRequiredMixin, TemplateView):
    template_name = "blackbaud/index.html"


class AdviseeReport(PermissionRequiredMixin, TemplateView):
    template_name = "blackbaud/advisee_report.html"

    permission_required = "blackbaud.view_advisor_list_report"

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        advisees = get_advisees()
        advisee_list = sorted(
            advisees,
            key=lambda pair: (pair.student.family_name, pair.student.given_name),
        )

        advisees_by_advisor: DefaultDict[Teacher, List[Student]] = defaultdict(list)
        for pair in advisees:
            advisees_by_advisor[pair.teacher].append(pair.student)

        advisees_by_advisor_list = sorted(
            advisees_by_advisor.items(),
            key=lambda pair: (
                pair[0].family_name,
                pair[0].given_name,
            ),  # Sort on teacher last name, first name
        )

        context["advisee_list"] = advisee_list
        context["advisees_by_advisor"] = advisees_by_advisor_list

        return context
