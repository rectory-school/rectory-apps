"""Admin for accounts"""

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from django import forms
from django.http import HttpRequest

from . import models


class AddUserFormWithoutPassword(forms.ModelForm):
    """Add a user without a password"""

    # This really just overrides clean so it isn't checking for passwords.
    # This is mainly because users of the app are expected to log in via Google,
    # which will correlate to the existing user and log in. Creating the user
    # before hand allows them to be assigned permissions, as the Google sign-in
    # process will create a user without a password anyway

    model = models.User


@admin.register(models.User)
class UserAdmin(DjangoUserAdmin):
    """Admin user model"""

    add_form = AddUserFormWithoutPassword
    actions = ["clear_password"]

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name'),
        }),
    )

    list_display = ('email', 'first_name', 'last_name', 'has_password')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

    @admin.display(boolean=True)
    def has_password(self, obj: models.User = None):
        """Determine if the user can log in directly"""

        return obj.password != ""

    def clear_password(self, request: HttpRequest, queryset):
        """Clear the user's password to force a Google login"""

        if request.user.is_authenticated and request.user in queryset and request.user.password != "":
            messages.warning(request, "You cannot clear a password on your own account")
            queryset = queryset.exclude(pk=request.user.pk)

        queryset.update(password='')
