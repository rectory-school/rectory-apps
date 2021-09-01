"""SIS Admin"""

from django.contrib import admin


class ViewOnlyAdmin(admin.ModelAdmin):
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
