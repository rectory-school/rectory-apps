"""Admin for stored email"""

from django.contrib import admin

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


class SendAddressInline(admin.TabularInline):
    """Inline for a send address"""

    model = models.SendAddress


@admin.register(models.OutgoingMessage)
class OutgoingMailAdmin(ViewOnlyAdminMixin, admin.ModelAdmin):
    """Admin for outgoing mail"""

    inlines = [SendAddressInline]
    list_filter = ['sent_at', 'created_at']
    list_display = ['pk', 'subject', 'created_at', 'sent_at']

    fields = ['from_name', 'from_address', 'reply_to_name', 'reply_to_address', 'subject', 'sent_at', 'mime']
    readonly_fields = ['mime']

    @admin.display(description='MIME Message')
    def mime(self, obj: models.OutgoingMessage = None) -> str:
        if obj:
            return str(obj.get_mime())
