"""Admin for calendar"""

from django.contrib import admin
from django import forms

from adminsortable2.admin import SortableInlineAdminMixin, SortableAdminBase


from . import models


class DayInline(SortableInlineAdminMixin, admin.TabularInline):
    """Inline for a day in a calendar"""

    model = models.Day
    extra = 0


class SkipDateInline(admin.TabularInline):
    """Inline for a skip date range in a calendar"""

    model = models.SkipDate
    extra = 0


class DateLabelInline(admin.TabularInline):
    """Inline for a label in a calendar"""

    model = models.ArbitraryLabel
    extra = 0


class ResetDayAdminFormset(forms.BaseInlineFormSet):
    """Override reset day admin formset to get a reference to the parent"""

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs["parent_object"] = self.instance

        return kwargs


class ResetDayAdminInlineForm(forms.ModelForm):
    """Form that accepts the parent object form arg"""

    def __init__(self, *args, parent_object: models.Calendar, **kwargs):
        super().__init__(*args, **kwargs)

        if parent_object.pk:
            # Restrict the days to those in this calendar
            self.fields["day"].choices = (
                (obj.pk, obj.letter) for obj in parent_object.days.all()
            )

    class Meta:
        model = models.ResetDay
        fields = ["date", "day"]


class ResetDayAdmin(admin.TabularInline):
    """Reset the calendar to a given day"""

    formset = ResetDayAdminFormset
    form = ResetDayAdminInlineForm
    model = models.ResetDay
    extra = 0


@admin.register(models.Calendar)
class CalendarAdmin(SortableAdminBase, admin.ModelAdmin):
    """Admin for a calendar"""

    inlines = [DayInline, SkipDateInline, ResetDayAdmin, DateLabelInline]


@admin.register(models.Color)
class RGBColorAdmin(admin.ModelAdmin):
    """Admin for colors"""


@admin.register(models.ColorSet)
class ColorSetAdmin(admin.ModelAdmin):
    """Color set admin"""

    save_as = True


@admin.register(models.Layout)
class LayoutAdmin(admin.ModelAdmin):
    """Layout admin"""

    save_as = True


@admin.register(models.MonthlyDisplaySet)
class MonthlyDisplaySetAdmin(admin.ModelAdmin):
    """Monthly display set admin"""


@admin.register(models.OnePageDisplaySet)
class OnePageDisplaySetAdmin(admin.ModelAdmin):
    """One page display set admin"""
