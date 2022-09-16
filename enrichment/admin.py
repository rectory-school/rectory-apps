from django.contrib import admin

from enrichment import models


@admin.register(models.Slot)
class SlotAdmin(admin.ModelAdmin):
    """Admin for slots"""


@admin.register(models.Option)
class OptionAdmin(admin.ModelAdmin):
    """Admin for slot options"""

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


@admin.register(models.Signup)
class SignupAdmin(admin.ModelAdmin):
    """Signup admin"""
