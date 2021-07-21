"""Icon system admin"""

from django.contrib import admin

from adminsortable2.admin import SortableInlineAdminMixin


from . import models


class PageIconInline(SortableInlineAdminMixin, admin.TabularInline):
    """Inline for page icons"""

    model = models.PageIconDisplay
    extra = 0


@admin.register(models.Page)
class PageAdmin(admin.ModelAdmin):
    """Admin for icon page"""

    inlines = [PageIconInline]

    prepopulated_fields = {"slug": ("title",)}


@admin.register(models.Icon)
class IconAdmin(admin.ModelAdmin):
    """Admin for icons"""
