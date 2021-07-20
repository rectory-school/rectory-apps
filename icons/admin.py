"""Icon system admin"""

from django.contrib import admin

from sorl.thumbnail.admin import AdminImageMixin


from . import models


class PageIconInline(admin.TabularInline):
    """Inline for page icons"""

    model = models.PageIconDisplay
    extra = 0


@admin.register(models.Page)
class PageAdmin(admin.ModelAdmin):
    """Admin for icon page"""

    inlines = [PageIconInline]

    prepopulated_fields = {"slug": ("title",)}


@admin.register(models.Icon)
class IconAdmin(AdminImageMixin, admin.ModelAdmin):
    """Admin for icons"""
