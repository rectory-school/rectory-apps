"""Template context processors for accounts"""

from .admin_staff_monkeypatch import patched_has_permission


def has_admin_access(request):
    """Add in the has_admin_access template variable"""

    return {
        'has_admin_access': patched_has_permission(request)
    }
