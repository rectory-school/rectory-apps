from datetime import date, datetime, timedelta
from typing import Iterator, Sequence
from zoneinfo import ZoneInfo

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from simple_history.models import HistoricalRecords

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

EMAIL_REPORT_CHOICES = (
    ("unassigned_advisor", "Unassigned advisees to advisors"),
    ("unassigned_admin", "Unassigned advisees to admins"),
    ("advisor_signups", "Advisee locations to advisors"),
    ("advisee_signups", "Advisee locations to advisees"),
    ("facilitator_signups", "Advisee locations to facilitators"),
    ("all_signups", "Full signup report"),
)

# Originally this used get_available_timezones, but that caused an issue in
# CI/CD checking for hanging migrations, since get_available_timezones() was
# returning different values in GitHub actions
TIMEZONE_CHOICES = tuple(
    (s, s)
    for s in (
        "America/New_York",
        "America/Chicago",
        "America/Denver",
        "America/Phoenix",
        "America/Los_Angeles",
        "America/Anchorage",
        "America/Adak",
        "Pacific/Honolulu",
        "UTC",
    )
)

RELATED_ADDRESS_CHOICES = (
    ("to", "To"),
    ("cc", "Cc"),
    ("bcc", "Bcc"),
    ("reply-to", "Reply To"),
)


def _choice_length(opts: Sequence[tuple[str, str]]):
    return max(len(p[0]) for p in opts)


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


class EmailConfig(models.Model):
    """General configs for email"""

    from_name = models.CharField(
        max_length=256,
        help_text="The name this email should be sent from",
    )

    from_address = models.EmailField(
        help_text="The address this email should be sent from",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    last_sent = models.DateTimeField(
        help_text="The time this email was last sent",
        null=True,
    )

    report = models.CharField(
        choices=EMAIL_REPORT_CHOICES,
        max_length=_choice_length(EMAIL_REPORT_CHOICES),
    )

    enabled = models.BooleanField(default=True)

    start = models.PositiveSmallIntegerField(
        help_text="How many days ahead we should start looking for slots",
        default=0,
    )

    end = models.PositiveSmallIntegerField(
        help_text="How many days ahead we should stop looking for slots",
        default=0,
    )

    timezone = models.CharField(
        choices=TIMEZONE_CHOICES,
        max_length=_choice_length(TIMEZONE_CHOICES),
        default=timezone.get_current_timezone_name,
    )

    time = models.TimeField()
    monday = models.BooleanField()
    tuesday = models.BooleanField()
    wednesday = models.BooleanField()
    thursday = models.BooleanField()
    friday = models.BooleanField()
    saturday = models.BooleanField()
    sunday = models.BooleanField()

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.get_report_display()}: {', '.join(self.weekday_labels)} at {self.time}"

    @property
    def weekday_flags(self) -> tuple[bool, bool, bool, bool, bool, bool, bool]:
        """True/false flags for each day of the week, starting with Monday"""

        return (
            self.monday,
            self.tuesday,
            self.wednesday,
            self.thursday,
            self.friday,
            self.saturday,
            self.sunday,
        )

    @property
    def weekday_labels(self) -> list[str]:
        labels = [
            _("Monday"),
            _("Tuesday"),
            _("Wednesday"),
            _("Thursday"),
            _("Friday"),
            _("Saturday"),
            _("Sunday"),
        ]

        return [str(l) for i, l in enumerate(labels) if self.weekday_flags[i]]

    @property
    def weekday_ints(self) -> set[int]:
        """Set if weekday integers with Monday being 0"""

        return {i for i in range(7) if self.weekday_flags[i]}

    @property
    def upcoming_send_times(self) -> Iterator[datetime]:
        if self.weekday_flags == (False, False, False, False, False, False, False):
            return

        tzinfo = ZoneInfo(self.timezone)

        today = date.today()
        effective_last_sent: datetime = self.created_at
        if self.last_sent:
            effective_last_sent = self.last_sent

        if not effective_last_sent:
            return

        dt = datetime(
            effective_last_sent.year,
            effective_last_sent.month,
            effective_last_sent.day,
            self.time.hour,
            self.time.minute,
            self.time.second,
            tzinfo=tzinfo,
        )

        while True:
            dt += timedelta(days=1)

            if dt < effective_last_sent:
                continue

            if dt.weekday() in self.weekday_ints:
                yield dt

    @property
    def next_run(self) -> datetime | None:
        if not self.enabled:
            return None

        try:
            return next(self.upcoming_send_times)
        except StopIteration:
            return None


class RelatedAddress(models.Model):
    """Related addresses for email configs"""

    name = models.CharField(max_length=255)
    address = models.EmailField()
    message = models.ForeignKey(
        EmailConfig,
        on_delete=models.CASCADE,
        related_name="addresses",
    )
    field = models.CharField(
        choices=RELATED_ADDRESS_CHOICES,
        max_length=_choice_length(RELATED_ADDRESS_CHOICES),
    )

    def __str__(self):
        return f"{self.get_field_display()}: {self.address}"
