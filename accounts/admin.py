"""Admin for accounts"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from django import forms

from .models import User


class AddUserFormWithoutPassword(forms.ModelForm):
    """Add a user without a password"""

    # This really just overrides clean so it isn't checking for passwords.
    # This is mainly because users of the app are expected to log in via Google,
    # which will correlate to the existing user and log in. Creating the user
    # before hand allows them to be assigned permissions, as the Google sign-in
    # process will create a user without a password anyway

    model = User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Admin user model"""

    add_form = AddUserFormWithoutPassword

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

    list_display = ('email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
