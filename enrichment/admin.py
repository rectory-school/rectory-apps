from datetime import date, datetime, time, timedelta
from typing import Optional
from django.contrib import admin
from django.contrib.admin.widgets import AdminSplitDateTime
from django import forms
from django.utils import timezone

from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Count
from django import forms
from enrichment import models


class DateFilter(admin.SimpleListFilter):
    title = _("date")
    parameter_name = "date"

    def lookups(self, request, model_admin):
        return (
            ("future", _("Future")),
            ("past", _("Past")),
        )

    def queryset(self, request, queryset):
        if self.value() == "future":
            return queryset.filter(date__gte=date.today())

        if self.value() == "past":
            return queryset.filter(date__lt=date.today())

        return queryset


class SlotForm(forms.ModelForm):
    editable_until = forms.SplitDateTimeField(
        required=False, widget=AdminSplitDateTime()
    )

    class Meta:
        model = models.Slot
        fields = "__all__"


@admin.register(models.Slot)
class SlotAdmin(admin.ModelAdmin):
    """Admin for slots"""

    list_filter = [DateFilter]
    form = SlotForm
    list_display = ["__str__", "date", "weekday", "editable_until"]
    actions = ["reset_edit_time"]

    def save_model(self, request, obj: models.Slot, form, change) -> None:
        if not obj.editable_until:
            obj.editable_until = default_editable_until(
                obj.date,
                timezone.get_current_timezone(),
            )
        return super().save_model(request, obj, form, change)

    @admin.action(description="Reset edit time")
    def reset_edit_time(self, request, queryset):
        for slot in queryset:
            assert isinstance(slot, models.Slot)

            slot.editable_until = default_editable_until(
                slot.date, timezone.get_current_timezone()
            )
            slot.save()

    @admin.display(description="Weekday")
    def weekday(self, obj: models.Slot) -> str:
        return obj.date.strftime("%A")


class OptionAvailableFilter(admin.SimpleListFilter):
    title = _("available")
    parameter_name = "available"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Current available")),
            ("no", _("Not currently available")),
        )

    def queryset(self, request, queryset):
        today = date.today()

        available_query = Q(start_date__lte=today) & (
            Q(end_date__isnull=True) | Q(end_date__gte=today)
        )

        if self.value() == "yes":
            return queryset.filter(available_query)

        if self.value() == "no":
            return queryset.filter(~available_query)

        return queryset


@admin.register(models.Option)
class OptionAdmin(admin.ModelAdmin):
    """Admin for slot options"""

    list_display = ["__str__", "disp_signup_count"]
    actions = ["disable_today", "remove_end_date"]
    list_filter = [OptionAvailableFilter, "end_date"]
    save_on_top = True
    autocomplete_fields = ("teacher",)
    filter_horizontal = (
        "only_available_on",
        "not_available_on",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "teacher",
                    "location",
                    "description",
                    "start_date",
                    "end_date",
                )
            },
        ),
        (
            "Limits",
            {
                "fields": (
                    "admin_only",
                    "only_available_on",
                    "not_available_on",
                ),
            },
        ),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("teacher")
        qs = qs.annotate(signup_count=Count("signup"))

        return qs

    @admin.action(description=_("Set end date to today"))
    def disable_today(self, request, queryset):
        queryset.update(end_date=date.today())

    @admin.action(description=_("Remove end date"))
    def remove_end_date(self, request, queryset):
        queryset.update(end_date=None)

    def has_delete_permission(self, request, obj=None) -> bool:
        # signup_count is added to the queryset in the admin model
        if obj and obj.signup_count > 0:
            return False

        return super().has_delete_permission(request, obj)

    @admin.decorators.display(description="All time signups", ordering="signup_count")
    def disp_signup_count(self, obj):
        return obj.signup_count


class SignupDateFilter(admin.SimpleListFilter):
    title = _("date")
    parameter_name = "date"

    def lookups(self, request, model_admin):
        return (
            ("future", _("Future")),
            ("past", _("Past")),
        )

    def queryset(self, request, queryset):
        if self.value() == "future":
            return queryset.filter(slot__date__gte=date.today())

        if self.value() == "past":
            return queryset.filter(slot__date__lt=date.today())

        return queryset


@admin.register(models.Signup)
class SignupAdmin(admin.ModelAdmin):
    """Signup admin"""

    list_filter = (SignupDateFilter, "option__teacher")
    search_fields = (
        "option__teacher__family_name",
        "option__teacher__given_name",
        "student__given_name",
        "student__family_name",
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("slot", "student", "option", "option__teacher")
        )


@admin.register(models.EditConfig)
class EditConfigAdmin(admin.ModelAdmin):
    """Config for editable config"""

    list_display = ["__str__", "days_before", "time"]


def default_editable_until(for_date: date, tzinfo) -> datetime:
    weekday = for_date.weekday()

    # Default to midnight UTC the day before

    try:
        config: models.EditConfig = models.EditConfig.objects.get(weekday=weekday)
        out = datetime.combine(for_date, config.time)
        out += timedelta(days=config.days_before * -1)
        return tzinfo.localize(out)

    except models.EditConfig.DoesNotExist:
        out = datetime.combine(for_date + timedelta(days=-1), time(23, 59, 59))
        return tzinfo.localize(out)


class RelatedAddressInline(admin.TabularInline):
    model = models.RelatedAddress


@admin.register(models.EmailConfig)
class EmailConfigAdmin(admin.ModelAdmin):
    """Email config admin"""

    inlines = [RelatedAddressInline]

    readonly_fields = ("last_sent", "next_run")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "report",
                    "start",
                    "end",
                    "enabled",
                    "last_sent",
                    "next_run",
                )
            },
        ),
        (
            "From",
            {
                "fields": (
                    "from_name",
                    "from_address",
                ),
            },
        ),
        (
            "Scheduling",
            {
                "fields": (
                    "timezone",
                    "time",
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                    "saturday",
                    "sunday",
                ),
            },
        ),
    )

    @admin.display(description="Next send")
    def next_run(self, obj: models.EmailConfig):
        val = obj.next_run

        if not val:
            return None

        return val
