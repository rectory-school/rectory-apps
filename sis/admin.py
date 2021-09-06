"""SIS Admin"""

from django.contrib import admin
from django.views.generic.base import View

from solo.admin import SingletonModelAdmin

from . import models


class ViewOnlyAdminMixin:
    """Admin view for mixin that provides view-only access"""

    def has_add_permission(self, request) -> bool:
        del request

        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        del request, obj

        return False

    def has_change_permission(self, request, obj=None) -> bool:
        del request, obj

        return False


@admin.register(models.Config)
class ConfigAdmin(SingletonModelAdmin):
    """Admin for the SIS configurations"""


@admin.register(models.AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    """Academic year admin"""


@admin.register(models.Student)
class StudentAdmin(ViewOnlyAdminMixin, admin.ModelAdmin):
    """Read-only student admin"""


@admin.register(models.Teacher)
class TeacherAdmin(ViewOnlyAdminMixin, admin.ModelAdmin):
    """View-only teacher admin"""

    list_filter = ['active']
    list_display = ['name', 'email', 'active']


@admin.register(models.Dorm)
class DormAdmin(admin.ModelAdmin):
    """Dorm admin"""


@admin.register(models.Grade)
class GradeAdmin(ViewOnlyAdminMixin, admin.ModelAdmin):
    """View only grade admin"""


@admin.register(models.Enrollment)
class EnrollmentAdmin(ViewOnlyAdminMixin, admin.ModelAdmin):
    """View only enrollment admin"""

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related('student', 'academic_year')

    list_display = ['__str__', 'boarder']
    list_filter = ['academic_year', 'boarder', 'status_attending', 'status_enrollment']


@admin.register(models.Course)
class CourseAdmin(ViewOnlyAdminMixin, admin.ModelAdmin):
    """View only course admin"""


@admin.register(models.Section)
class SectionAdmin(ViewOnlyAdminMixin, admin.ModelAdmin):
    """View only section admin"""

    # TODO: Select academic year in the queryset


@admin.register(models.StudentRegistration)
class StudentRegistrationAdmin(ViewOnlyAdminMixin, admin.ModelAdmin):
    """View only student registration admin"""

    # TODO: Select academic year, section and student in the queryset


@admin.register(models.Parent)
class ParentAdmin(ViewOnlyAdminMixin, admin.ModelAdmin):
    """View only parent admin"""

    list_display = ['full_id', 'full_name', 'first_name', 'last_name']
