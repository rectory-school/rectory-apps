from datetime import date
from typing import Any, List, Tuple
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

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


@admin.register(models.Slot)
class SlotAdmin(admin.ModelAdmin):
    """Admin for slots"""

    list_filter = [DateFilter]


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
                    "only_available_on",
                    "not_available_on",
                ),
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("teacher")

    @admin.action(description=_("Set end date to today"))
    def disable_today(self, request, queryset):
        queryset.update(end_date=date.today())

    @admin.action(description=_("Remove end date"))
    def remove_end_date(self, request, queryset):
        queryset.update(end_date=None)


@admin.register(models.Signup)
class SignupAdmin(admin.ModelAdmin):
    """Signup admin"""

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("slot", "student", "option")
