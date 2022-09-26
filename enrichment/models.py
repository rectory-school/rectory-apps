from django.db import models
from django.utils import timezone

from simple_history.models import HistoricalRecords

from solo.models import SingletonModel
from blackbaud.models import Teacher, Student

WEEKDAY_CHOICES = (
    (0, "Monday"),
    (1, "Tuesday"),
    (2, "Wednesday"),
    (3, "Thursday"),
    (4, "Friday"),
    (5, "Saturday"),
    (6, "Sunday"),
)


class Slot(models.Model):
    """A time slot that Enrichment will run on"""

    date = models.DateField(db_index=True)
    title = models.CharField(
        max_length=256,
        blank=True,
        help_text="Any secondary description for this enrichment slot, generally not required",
    )
    editable_until = models.DateTimeField(
        help_text="When this slot will be locked out", default=timezone.now
    )
    active = models.BooleanField(default=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ["date", "title"]

    def __str__(self):
        if self.title:
            return f"{self.date}: {self.title}"

        return f"{self.date}"


class Option(models.Model):
    """An enrichment option that students can be sent to"""

    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    location = models.CharField(max_length=256)
    description = models.CharField(max_length=4096, blank=True)

    admin_only = models.BooleanField(
        default=False,
        help_text="If this option should only be assignable by admin users",
    )

    only_available_on = models.ManyToManyField(
        Slot,
        help_text="An exclusive list of slots this option should be available on",
        related_name="+",
        blank=True,
    )

    not_available_on = models.ManyToManyField(
        Slot,
        help_text="A list of slots this option should not be available on",
        related_name="+",
        blank=True,
    )

    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(blank=True, null=True)

    history = HistoricalRecords()

    def __str__(self):
        teacher: Teacher = self.teacher
        if self.description:
            return f"{teacher.formal_name}: {self.description} in {self.location}"

        return f"{teacher.formal_name}: {self.location}"


class LocationOverride(models.Model):
    """An overridden location for a single option on a single day"""

    slot = models.ForeignKey(Slot, on_delete=models.CASCADE)
    option = models.ForeignKey(
        Option,
        on_delete=models.CASCADE,
        related_name="location_overrides",
    )

    location = models.CharField(max_length=256)

    class Meta:
        unique_together = (("slot", "option"),)


class Signup(models.Model):
    """A student signed up for a slot"""

    slot = models.ForeignKey(Slot, on_delete=models.CASCADE, db_index=True)
    option = models.ForeignKey(Option, on_delete=models.DO_NOTHING, db_index=True)
    student = models.ForeignKey(Student, on_delete=models.DO_NOTHING, db_index=True)
    admin_locked = models.BooleanField()

    history = HistoricalRecords()

    class Meta:
        unique_together = (("slot", "student"),)
        permissions = (
            (
                "edit_past_lockout",
                "Can edit enrichment signups past the lockout time",
            ),
            (
                "set_admin_locked",
                "Can set/unset admin locked, as well as ignore the flag usage",
            ),
            (
                "use_admin_only_options",
                "Can assign students to admin only options",
            ),
            (
                "assign_all_advisees",
                "Can assign any advisees",
            ),
        )

    def __str__(self):
        return f"{self.slot}/{self.student}: {self.option}"


class EditConfig(models.Model):

    weekday = models.SmallIntegerField(
        choices=WEEKDAY_CHOICES,
        unique=True,
        help_text="What weekday this applies to",
    )
    days_before = models.PositiveSmallIntegerField(
        help_text="How many days before the slot date the lockout should be effective",
    )
    time = models.TimeField(
        help_text="When the slot should be locked out",
    )

    def __str__(self):
        return self.get_weekday_display()
