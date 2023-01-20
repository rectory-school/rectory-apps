from django.db import models
from django.utils import timezone

from blackbaud.models import Student


class QuestionSet(models.Model):
    """A set of questions assignable to evaluations"""

    name = models.CharField(max_length=256)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class FreeformQuestion(models.Model):
    """A freeform question inside of a question set"""

    question_set = models.ForeignKey(
        QuestionSet,
        on_delete=models.CASCADE,
        related_name="freeform_questions",
    )
    required = models.BooleanField(default=False)
    position = models.PositiveSmallIntegerField()
    question = models.TextField()

    class Meta:
        ordering = ("position",)

    def __str__(self):
        return self.question


class MultipleChoiceQuestion(models.Model):
    """A multiple choice question inside of a question set"""

    question_set = models.ForeignKey(
        QuestionSet,
        on_delete=models.CASCADE,
        related_name="multiple_choice_questions",
    )
    required = models.BooleanField(default=True)
    position = models.PositiveSmallIntegerField()
    question = models.TextField()

    class Meta:
        ordering = ("position",)

    def __str__(self):
        return self.question


class MultipleChoiceAnswer(models.Model):
    """An available answer to a multiple choice question"""

    question = models.ForeignKey(
        MultipleChoiceQuestion,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    position = models.PositiveSmallIntegerField()
    answer = models.CharField(max_length=50)

    class Meta:
        ordering = ("position",)

    def __str__(self):
        return self.answer


class TagCategory(models.Model):
    """A tag category, such as 'evaluation type', 'teacher',
    'class', 'year', or similar"""

    name = models.CharField(max_length=256, unique=True)
    system_managed = models.BooleanField(default=False)

    admin_filter_display_values = models.BooleanField(
        default=False,
        help_text=(
            "If the individual values for this tag category "
            "should be listed on the admin filter"
        ),
    )

    admin_filter_breakout_values = models.BooleanField(
        default=False,
        help_text=(
            "If the individual values for this tag category "
            "should be broken out on the admin filter"
        ),
    )

    def __str__(self):
        return self.name


class TagManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related("category")
        return qs


class Tag(models.Model):
    """A single tag, such as class: 5 math"""

    category = models.ForeignKey(
        TagCategory,
        on_delete=models.CASCADE,
        related_name="tags",
    )
    value = models.CharField(max_length=256, db_index=True)

    objects = TagManager()

    class Meta:
        unique_together = (("category", "value"),)

    def __str__(self):
        return f"{self.category}: {self.value}"


class Evaluation(models.Model):
    """An evaluation request"""

    name = models.CharField(max_length=256)
    student = models.ForeignKey(Student, on_delete=models.DO_NOTHING)
    question_set = models.ForeignKey(QuestionSet, on_delete=models.DO_NOTHING)
    tags = models.ManyToManyField(Tag, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    available_starting_at = models.DateTimeField(blank=True, null=True)
    available_until = models.DateTimeField(blank=True, null=True)

    @property
    def is_available(self) -> bool:
        if self.available_starting_at and timezone.now() < self.available_starting_at:
            return False

        if self.available_until and timezone.now() > self.available_until:
            return False

        return True

    def __str__(self):
        return self.name


class EvaluationMultipleChoiceAnswer(models.Model):
    """A selected answer for a multiple choice question"""

    evaluation = models.ForeignKey(
        Evaluation,
        on_delete=models.CASCADE,
        related_name="multiple_choice_answers",
    )
    answer = models.ForeignKey(MultipleChoiceAnswer, on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.answer.answer


class EvaluationFreeformAnswer(models.Model):
    """A selected answer for a freeform question"""

    evaluation = models.ForeignKey(
        Evaluation,
        on_delete=models.CASCADE,
        related_name="freeform_answers",
    )
    question = models.ForeignKey(FreeformQuestion, on_delete=models.DO_NOTHING)
    answer = models.TextField()

    def __str__(self):
        return self.answer


class LegacyQuestionSet(models.Model):
    question_set = models.OneToOneField(QuestionSet, on_delete=models.CASCADE)
    legacy_id = models.IntegerField(unique=True)


class LegacyFreeformQuestion(models.Model):
    freeform_question = models.OneToOneField(
        FreeformQuestion,
        on_delete=models.CASCADE,
    )
    legacy_id = models.IntegerField(unique=True)


class LegacyMultipleChoiceQuestion(models.Model):
    multiple_choice_question = models.OneToOneField(
        MultipleChoiceQuestion,
        on_delete=models.CASCADE,
    )
    legacy_id = models.IntegerField(unique=True)


class LegacyMultipleChoiceAnswer(models.Model):
    multiple_choice_answer = models.OneToOneField(
        MultipleChoiceAnswer,
        on_delete=models.CASCADE,
    )
    legacy_id = models.IntegerField(unique=True)


class ReportCategorizer(models.Model):
    name = models.CharField(max_length=256)

    def __str__(self):
        return self.name


class ReportCategorizerTagCategory(models.Model):
    categorizer = models.ForeignKey(ReportCategorizer, on_delete=models.CASCADE)
    position = models.PositiveIntegerField()
    category = models.ForeignKey(TagCategory, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("categorizer", "category"),)
        ordering = ("position",)

    def __str__(self):
        return f"{self.categorizer.name}: {self.category.name}"


class UploadConfiguration(models.Model):
    """A given upload configuration"""

    name = models.CharField(max_length=256)
    question_set = models.ForeignKey(QuestionSet, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class UploadConfigurationTagCategory(models.Model):
    """A single tag category in an upload configuration"""

    upload_configuration = models.ForeignKey(
        UploadConfiguration,
        on_delete=models.CASCADE,
    )
    category = models.ForeignKey(
        TagCategory,
        on_delete=models.CASCADE,
    )
    required = models.BooleanField(default=True)
    split = models.BooleanField(default=False)

    class Meta:
        ordering = ["category__name"]

    def __str__(self):
        return f"{self.upload_configuration}: {self.category.name}"
