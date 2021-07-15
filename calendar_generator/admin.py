"""Admin for calendar"""

from django.contrib import admin

from adminsortable2.admin import SortableInlineAdminMixin


from . import models


class DayInline(SortableInlineAdminMixin, admin.TabularInline):
    """Inline for a day in a calendar"""

    model = models.Day
    extra = 0


class SkipDateInline(admin.TabularInline):
    """Inline for a skip date range in a calendar"""

    model = models.SkipDate
    extra = 0


@admin.register(models.Calendar)
class CalendarAdmin(admin.ModelAdmin):
    """Admin for a calendar"""

    inlines = [DayInline, SkipDateInline]
