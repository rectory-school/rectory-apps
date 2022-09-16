from typing import Set

import humanize

from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext as _

from solo.admin import SingletonModelAdmin


from . import models


@admin.register(models.SyncConfig)
class SyncConfigAdmin(SingletonModelAdmin):
    fields = ["sync_enabled", "sync_asap", "last_sync_attempt", "get_sync_delay"]
    readonly_fields = ["last_sync_attempt", "get_sync_delay"]

    @admin.display(description="Time until next sync")
    def get_sync_delay(self, obj: models.SyncConfig):
        if obj.ready_for_sync:
            return _("ASAP")

        return humanize.naturaldelta(obj.next_sync - timezone.now())


class NoAdd(admin.ModelAdmin):
    """Block addition"""

    def has_add_permission(self, request):
        return False


class NoDelete(admin.ModelAdmin):
    """Block deletion"""

    def has_delete_permission(self, request, obj=None):
        return False


class NoChange(admin.ModelAdmin):
    """Block changes"""

    def has_change_permission(self, request, obj=None):
        return False


class ChangeOnly(NoAdd, NoDelete):
    """Change only permissions"""

    editable_fields: Set[str] = set()

    def get_fields(self, request, obj=None):
        if self.fields:
            return self.fields

        return [f.attname for f in obj._meta.fields if not f.auto_created]

    def get_readonly_fields(self, request, obj):
        fields = set(self.get_fields(request, obj))
        return list(fields - self.editable_fields)


class ReadOnly(NoAdd, NoDelete, NoChange):
    """Read only permissions"""


@admin.register(models.School)
class SchoolAdmin(ReadOnly):
    """Read-only school admin"""

    list_filter = ["active"]
    search_fields = ["name"]
    list_display = ["name", "sis_id", "active"]


@admin.register(models.Teacher)
class TeacherAdmin(ChangeOnly):
    editable_fields = {"honorific", "formal_name_override"}
    search_fields = ["given_name", "family_name", "email"]
    list_display = ["__str__", "given_name", "family_name", "email", "active"]
    list_filter = ["active", "schools"]


@admin.register(models.Student)
class StudentAdmin(ChangeOnly, admin.ModelAdmin):
    """Student admin"""

    editable_fields = {"nickname"}
    search_fields = ["given_name", "family_name", "email"]
    list_display = ["__str__", "given_name", "family_name", "email", "active"]
    list_filter = ["active", "schools"]


@admin.register(models.Course)
class CourseAdmin(ReadOnly, admin.ModelAdmin):
    search_fields = ["title"]


@admin.register(models.Class)
class ClassAdmin(ReadOnly, admin.ModelAdmin):
    search_fields = ["title", "course"]
    list_filter = ["course"]


@admin.register(models.TeacherEnrollment)
class TeacherEnrollmentAdmin(ReadOnly, admin.ModelAdmin):
    search_fields = [
        "teacher__given_name",
        "teacher__family_name",
        "section__course__title",
    ]
    list_filter = ["section__course"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("teacher", "section", "section__course")
        )


@admin.register(models.StudentEnrollment)
class StudentEnrollmentAdmin(ReadOnly, admin.ModelAdmin):
    search_fields = [
        "student__given_name",
        "student__family_name",
        "section__course__title",
    ]
    list_filter = ["section__course"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("student", "section", "section__course")
        )


@admin.register(models.AdvisoryCourse)
class AdvisoryClassAdmin(admin.ModelAdmin):
    """Advisory class admin"""

    autocomplete_fields = ["course"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("course")


@admin.register(models.AdvisorySchool)
class AdvisorySchoolAdmin(admin.ModelAdmin):
    """Advisory school admin"""

    autocomplete_fields = ["school"]
