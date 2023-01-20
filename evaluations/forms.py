from django import forms
from django.db import transaction
from django.utils import timezone

from . import models


class EvaluationForm(forms.Form):
    def __init__(self, evaluation: models.Evaluation, *args, **kwargs):
        self.evaluation = evaluation
        question_set = evaluation.question_set
        super().__init__(*args, **kwargs)

        self.freeform_question_keys: dict[str, int] = {}
        self.multiple_choice_questions_keys: set[str] = set()

        for multiple_choice_question in question_set.multiple_choice_questions.all():
            key = f"multiple-choice-question-{multiple_choice_question.pk}"
            self.multiple_choice_questions_keys.add(key)

            choices = [
                (obj.pk, obj.answer) for obj in multiple_choice_question.answers.all()
            ]

            self.fields[key] = forms.ChoiceField(
                label=multiple_choice_question.question,
                choices=choices,
                required=multiple_choice_question.required,
                widget=forms.RadioSelect(),
            )

        for freeform_question in question_set.freeform_questions.all():
            key = f"freeform-question-{freeform_question.pk}"
            self.freeform_question_keys[key] = freeform_question.pk

            self.fields[key] = forms.CharField(
                label=freeform_question.question,
                required=freeform_question.required,
                widget=forms.Textarea(),
            )

    def save_responses(self, *args, **kwargs):
        """Save the completed responses"""

        with transaction.atomic():
            self.evaluation.completed_at = timezone.now()
            self.evaluation.save()

            self.evaluation.multiple_choice_answers.all().delete()
            self.evaluation.freeform_answers.all().delete()

            for key in self.multiple_choice_questions_keys:
                answer_id = self.cleaned_data.get(key)

                if answer_id:
                    models.EvaluationMultipleChoiceAnswer.objects.create(
                        evaluation=self.evaluation,
                        answer_id=answer_id,
                    )

            for key, freeform_id in self.freeform_question_keys.items():
                answer = self.cleaned_data.get(key)

                if answer:
                    models.EvaluationFreeformAnswer.objects.create(
                        evaluation=self.evaluation,
                        question_id=freeform_id,
                        answer=answer,
                    )

        return
