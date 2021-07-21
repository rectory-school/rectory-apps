"""Icon system admin"""

from django.contrib import admin

from adminsortable2.admin import SortableInlineAdminMixin


from . import models


@admin.register(models.Icon)
class IconAdmin(admin.ModelAdmin):
    """Admin for icons"""


class PageItemInline(SortableInlineAdminMixin, admin.TabularInline):
    """Inline for page icons"""

    model = models.PageItem
    extra = 0


@admin.register(models.Page)
class PageAdmin(admin.ModelAdmin):
    """Admin for icon page"""

    inlines = [PageItemInline]

    prepopulated_fields = {"slug": ("title",)}


class FolderIconInline(SortableInlineAdminMixin, admin.TabularInline):
    """Inline for folder icons"""

    model = models.FolderIcon
    extra = 0


@admin.register(models.Folder)
class FolderAdmin(admin.ModelAdmin):
    """Admin for folders"""

    inlines = [FolderIconInline]
