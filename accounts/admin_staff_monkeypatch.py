"""Monkey patch the Django admin site to also allow a permission check"""

# I feel SO dirty doing this, but admin autodiscover doesn't work if I have a custom admin site,
# and all I want to do is allow you to get into the admin site if you have either the is_staff flag or
# a custom permission as defined on the accounts model. This is so that in migrations I can pre-create
# the groups for permissions, wherein some of those groups would need to grant the equivalent of the staff flag


def patched_has_permission(request) -> bool:
    """
    Patched version of admin site has_permission,
    to allow for the accounts:admin_login permission
    """

    if request.user.is_active:
        if request.user.is_staff:
            return True

        if request.user.is_superuser:
            return True

        # This was my custom addition
        if request.user.has_perm("accounts.admin_login"):
            return True

    return False
