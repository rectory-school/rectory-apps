from django.core.management import BaseCommand
from django.db import transaction

from evaluations import models

import json


def _existing_question_sets() -> dict[int, models.QuestionSet]:
    return {
        obj.legacyquestionset.legacy_id: obj
        for obj in models.QuestionSet.objects.filter(legacyquestionset__isnull=False)
    }


def _existing_freeform_questions() -> dict[int, models.FreeformQuestion]:
    return {
        obj.legacyfreeformquestion.legacy_id: obj
        for obj in models.FreeformQuestion.objects.filter(
            legacyfreeformquestion__isnull=False
        )
    }


def _existing_multiple_choice_questions() -> dict[int, models.MultipleChoiceQuestion]:
    return {
        obj.legacymultiplechoicequestion.legacy_id: obj
        for obj in models.MultipleChoiceQuestion.objects.filter(
            legacymultiplechoicequestion__isnull=False
        )
    }


def _existing_multiple_choice_answers() -> dict[int, models.MultipleChoiceAnswer]:
    return {
        obj.legacymultiplechoiceanswer.legacy_id: obj
        for obj in models.MultipleChoiceAnswer.objects.filter(
            legacymultiplechoiceanswer__isnull=False
        )
    }


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.records: list[dict] = []
        self.question_sets = _existing_question_sets()
        self.freeform_questions = _existing_freeform_questions()
        self.multiple_choice_questions = _existing_multiple_choice_questions()
        self.multiple_choice_answers = _existing_multiple_choice_answers()
        self.question_sets_by_id: dict[int, models.QuestionSet] = {}

    def add_arguments(self, parser) -> None:
        parser.add_argument("input_file")

    @transaction.atomic()
    def execute(self, *args, **kwargs):
        input_file: str = kwargs["input_file"]
        with open(input_file) as f_in:
            self.records = json.load(f_in)

        self.load_question_sets()
        self.load_freeform_questions()
        self.load_multiple_choice_questions()
        self.load_multiple_choice_answers()

    def load_question_sets(self):
        question_sets = (
            r for r in self.records if r["model"] == "courseevaluations.questionset"
        )

        for r in question_sets:
            name: str = r["fields"]["name"]
            pk: int = r["pk"]

            if pk not in self.question_sets:
                question_set = models.QuestionSet(name=name)
                question_set.save()
                self.question_sets_by_id[pk] = question_set
                models.LegacyQuestionSet.objects.create(
                    question_set=question_set,
                    legacy_id=pk,
                )
            else:
                question_set = self.question_sets[pk]

            question_set.name = name
            question_set.save()

    def load_freeform_questions(self):
        freeform_questions = (
            r
            for r in self.records
            if r["model"] == "courseevaluations.freeformquestion"
        )

        for r in freeform_questions:
            pk = r["pk"]
            question = r["fields"]["question"]
            position = r["fields"]["question_order"]

            if pk not in self.freeform_questions:
                obj = models.FreeformQuestion()
                obj.question = question
                obj.position = position
                obj.question_set = self.question_sets[r["fields"]["question_set"]]
                obj.save()

                models.LegacyFreeformQuestion.objects.create(
                    freeform_question=obj, legacy_id=pk
                )
                self.freeform_questions[pk] = obj

            obj = self.freeform_questions[pk]
            obj.question = question
            obj.position = position
            obj.question_set = self.question_sets[r["fields"]["question_set"]]
            obj.save()

    def load_multiple_choice_questions(self):
        multiple_choice_questions = (
            r
            for r in self.records
            if r["model"] == "courseevaluations.multiplechoicequestion"
        )

        for r in multiple_choice_questions:
            pk = r["pk"]
            question = r["fields"]["question"]
            position = r["fields"]["question_order"]

            if pk not in self.multiple_choice_questions:
                obj = models.MultipleChoiceQuestion()
                obj.question = question
                obj.position = position
                obj.question_set = self.question_sets[r["fields"]["question_set"]]
                obj.save()

                models.LegacyMultipleChoiceQuestion.objects.create(
                    multiple_choice_question=obj, legacy_id=pk
                )
                self.multiple_choice_questions[pk] = obj

            obj = self.multiple_choice_questions[pk]
            obj.question = question
            obj.position = position
            obj.question_set = self.question_sets[r["fields"]["question_set"]]
            obj.save()

    def load_multiple_choice_answers(self):
        multiple_choice_answers = (
            r
            for r in self.records
            if r["model"] == "courseevaluations.multiplechoicequestionoption"
        )

        for r in multiple_choice_answers:
            pk = r["pk"]

            question = self.multiple_choice_questions[r["fields"]["question"]]
            position = r["fields"]["option_order"]
            answer = r["fields"]["option"]

            if pk not in self.multiple_choice_answers:
                obj = models.MultipleChoiceAnswer()
                obj.question = question
                obj.position = position
                obj.answer = answer

                obj.save()

                models.LegacyMultipleChoiceAnswer.objects.create(
                    multiple_choice_answer=obj, legacy_id=pk
                )
                self.multiple_choice_answers[pk] = obj

            obj = self.multiple_choice_answers[pk]
            obj.question = question
            obj.position = position
            obj.answer = answer
            obj.save()
