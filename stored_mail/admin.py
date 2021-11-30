"""Admin for stored email"""

from django.contrib import admin

from . import models


class ViewOnlyAdminMixin:
    """Admin view for mixin that provides view-only access"""

    def has_add_permission(self, request) -> bool:
        """Nobody can add items to a view only model"""

        del request

        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        """Nobody can delete items from a view only model"""

        del request, obj

        return False

    def has_change_permission(self, request, obj=None) -> bool:
        """Nobody can change items on a view only model"""

        del request, obj

        return False


class RelatedAddressInline(admin.TabularInline):
    """Inline for a send address"""

    model = models.RelatedAddress


@admin.register(models.OutgoingMessage)
class OutgoingMailAdmin(ViewOnlyAdminMixin, admin.ModelAdmin):
    """Admin for outgoing mail"""

    inlines = [RelatedAddressInline]
    list_filter = ['sent_at', 'created_at', 'last_send_attempt']
    list_display = ['pk', 'subject', 'created_at', 'sent_at', 'last_send_attempt']

    fields = ['from_name', 'from_address', 'subject', 'sent_at', 'created_at', 'encoded']
    readonly_fields = ['encoded']

    @admin.display(description='Encoded Message')
    def encoded(self, obj: models.OutgoingMessage = None) -> str:
        """Encoded display helper"""

        if obj:
            return str(obj.get_django_email().message())