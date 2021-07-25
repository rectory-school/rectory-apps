"""Icon system admin"""

from django.contrib import admin
from django.http import HttpRequest
from django.db.models import QuerySet

from adminsortable2.admin import SortableInlineAdminMixin


from . import models


@admin.register(models.Icon)
class IconAdmin(admin.ModelAdmin):
    """Admin for icons"""


class PageTextLinkInline(admin.StackedInline):
    """Text link inline"""

    fk_name = 'page'
    model = models.CrossLink
    extra = 0


class PageIconInline(admin.TabularInline):
    """Page icon inline"""

    model = models.PageIcon
    extra = 0


class PageFolderInline(admin.TabularInline):
    """Page folder inline"""

    model = models.PageFolder
    extra = 0


@admin.register(models.Page)
class PageAdmin(admin.ModelAdmin):
    """Admin for icon page"""

    inlines = [PageIconInline, PageFolderInline, PageTextLinkInline]

    prepopulated_fields = {"slug": ("title",)}

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        qs = super().get_queryset(request)
        qs = qs.prefetch_related("page_icons", "page_icons__page", "page_icons__icon",
                                 "page_folders__folder", "page_folders__page")

        return qs


class FolderIconInline(SortableInlineAdminMixin, admin.TabularInline):
    """Inline for folder icons"""

    model = models.FolderIcon
    extra = 0


@admin.register(models.Folder)
class FolderAdmin(admin.ModelAdmin):
    """Admin for folders"""

    inlines = [FolderIconInline]
