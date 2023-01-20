from django.views.generic import TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse_lazy

from . import models
from . import forms


class EvaluationList(LoginRequiredMixin, TemplateView):
    """Evaluation landing page"""

    template_name = "evaluations/index.html"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)

        return {
            **self._evaluation_list(),
            **context,
        }

    def _evaluation_list(self) -> dict:
        student: Optional[models.Student] = self.request.student  # type: ignore

        if student:
            evaluations = models.Evaluation.objects.filter(student=student)
            complete_evaluations = evaluations.filter(completed_at__isnull=False)
            incomplete_evaluations = evaluations.filter(completed_at__isnull=True)

            q_starting_at_null = Q(available_starting_at__isnull=True)
            q_starting_at_before_now = Q(available_starting_at__lte=timezone.now())
            q_starting_at = q_starting_at_null | q_starting_at_before_now

            q_available_until_null = Q(available_until__isnull=True)
            q_available_until_after_now = Q(available_until__gt=timezone.now())
            q_available_until = q_available_until_null | q_available_until_after_now

            q_available = q_starting_at & q_available_until

            available_evaluations = incomplete_evaluations.filter(q_available)
            missed_evaluations = incomplete_evaluations.exclude(q_available)

            return {
                "completed_evaluations": complete_evaluations,
                "incomplete_evaluations": incomplete_evaluations,
                "available_evaluations": available_evaluations,
                "missed_evaluations": missed_evaluations,
            }

        return {
            "completed_evaluations": [],
            "incomplete_evaluations": [],
            "available_evaluations": [],
            "missed_evaluations": [],
        }


class CompleteEvaluation(LoginRequiredMixin, FormView):
    form_class = forms.EvaluationForm
    template_name = "evaluations/evaluation.html"
    success_url = reverse_lazy("evaluations:index")

    def dispatch(self, request, *args, **kwargs):
        to_prefetch = (
            "question_set",
            "question_set__multiple_choice_questions",
            "question_set__multiple_choice_questions__answers",
            "question_set__freeform_questions",
        )

        self.evaluation = get_object_or_404(
            models.Evaluation.objects.prefetch_related(*to_prefetch),
            pk=self.kwargs["pk"],
            student=request.student,
        )

        return super().dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        if not self.form_completable:
            return redirect(self.success_url)

        return super().get(*args, **kwargs)

    def post(self, *args, **kwargs):
        if not self.form_completable:
            messages.error(self.request, "Your survey was not able to be completed")
            return redirect(self.success_url)

        return super().post(*args, **kwargs)

    def get_form_kwargs(self) -> dict:
        kwargs = super().get_form_kwargs()
        kwargs["evaluation"] = self.evaluation
        return kwargs

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context["evaluation"] = self.evaluation
        return context

    def form_valid(self, form: forms.EvaluationForm):
        form.save_responses()
        messages.success(self.request, "Thank you for completing your evaluation")
        return super().form_valid(form)

    @property
    def form_completable(self) -> bool:
        if self.evaluation.completed_at:
            return False

        if not self.evaluation.is_available:
            return False

        return True
