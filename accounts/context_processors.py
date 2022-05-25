"""Template context processors for accounts"""

from django.urls import reverse
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME

from .admin_staff_monkeypatch import patched_has_permission


def account_processors(request):
    """Add in the has_admin_access template variable"""

    login_url = reverse('accounts:login')
    full_login_url = request.build_absolute_uri(login_url)
    redirect_to = request.GET.get(REDIRECT_FIELD_NAME) or request.path

    return {
        'has_admin_access': patched_has_permission(request),
        'google_login_url': full_login_url,
        'google_oauth_client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
        'google_redirect_to': redirect_to
    }
