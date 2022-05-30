"""Template context processors for accounts"""

from django.http import HttpRequest
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME

from .admin_staff_monkeypatch import patched_has_permission

from .views import USER_DID_LOGOUT_KEY


def account_processors(request: HttpRequest):
    """Add in the has_admin_access template variable"""

    login_url = reverse("accounts:login")
    full_login_url = request.build_absolute_uri(login_url)
    redirect_to = request.GET.get(REDIRECT_FIELD_NAME) or request.path

    currently_logged_in = request.user.is_authenticated
    did_logout = request.session.get(USER_DID_LOGOUT_KEY, False)

    out = {
        "has_admin_access": patched_has_permission(request),
        "google_login_url": full_login_url,
        "google_oauth_client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
        "google_redirect_to": redirect_to,
        "redirect_field_name": REDIRECT_FIELD_NAME,
    }

    # This is conditionally set because a template context might set it.
    # If it had been set to false, we would override the template's context
    if did_logout or currently_logged_in:
        out["disable_auto_login"] = True

    return out
