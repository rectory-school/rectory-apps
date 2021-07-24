"""Icon system admin"""

from django.contrib import admin

from adminsortable2.admin import SortableInlineAdminMixin


from . import models


@admin.register(models.Icon)
class IconAdmin(admin.ModelAdmin):
    """Admin for icons"""


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

    inlines = [PageIconInline, PageFolderInline]

    prepopulated_fields = {"slug": ("title",)}


class FolderIconInline(SortableInlineAdminMixin, admin.TabularInline):
    """Inline for folder icons"""

    model = models.FolderIcon
    extra = 0


@admin.register(models.Folder)
class FolderAdmin(admin.ModelAdmin):
    """Admin for folders"""

    inlines = [FolderIconInline]
