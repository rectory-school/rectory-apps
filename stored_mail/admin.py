"""Admin for stored email"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

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


class ExtraHeaderInline(admin.TabularInline):
    """Inline for extra headers"""

    model = models.ExtraHeader


class OutgoingMailAdminSentStatus(admin.SimpleListFilter):
    """Basic filter for outgoing mail status"""

    title = _("status")
    parameter_name = "status"

    def lookups(self, request, model_admin):
        return (
            ("sent", _("Sent")),
            ("unsent", _("Unsent")),
            ("discarded", _("Discarded")),
        )

    def queryset(self, request, queryset):
        if self.value() == "sent":
            return queryset.filter(sent_at__isnull=False)

        if self.value() == "discarded":
            return queryset.filter(
                sent_at__isnull=True, discard_after__lte=timezone.now()
            )

        if self.value() == "unsent":
            return queryset.filter(
                sent_at__isnull=True, discard_after__gt=timezone.now()
            )


@admin.register(models.OutgoingMessage)
class OutgoingMailAdmin(ViewOnlyAdminMixin, admin.ModelAdmin):
    """Admin for outgoing mail"""

    inlines = [RelatedAddressInline, ExtraHeaderInline]
    list_filter = [OutgoingMailAdminSentStatus, "sent_at", "created_at"]
    list_display = ["pk", "subject", "created_at", "sent_at", "last_send_attempt"]

    fields = [
        "from_name",
        "from_address",
        "subject",
        "created_at",
        "discard_after",
        "last_send_attempt",
        "sent_at",
        "encoded",
    ]
    readonly_fields = ["encoded"]

    @admin.display(description="Encoded Message")
    def encoded(self, obj: models.OutgoingMessage = None) -> str:
        """Encoded display helper"""

        if obj:
            return str(obj.get_django_email().message())

        return ""
