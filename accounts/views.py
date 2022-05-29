"""Accounts views"""

from typing import Dict, Any

import structlog

from google.oauth2 import id_token
from google.auth.transport import requests

from django.http.response import HttpResponseRedirect, HttpResponseBase
from django.http import HttpRequest
from django.contrib.auth.views import LoginView
from django.contrib.auth import REDIRECT_FIELD_NAME, logout as auth_logout
from django.views.generic import TemplateView
from django.contrib.auth import get_user_model, login
from django.http import JsonResponse
from django.urls import reverse
from django.contrib import messages

from django.utils.translation import gettext_lazy as _

from django.conf import settings

log = structlog.get_logger()

UserModel = get_user_model()

LOGIN_REDIRECT_URL = settings.LOGIN_REDIRECT_URL
USER_DID_LOGOUT_KEY = "user_did_logout"
bypass_hd_check_on_existing_email = settings.GOOGLE_BYPASS_HD_CHECK_ON_EMAIL

allowed_domains = [domain.lower() for domain in settings.GOOGLE_HOSTED_DOMAINS]


class SocialLoginView(TemplateView):
    """Handle social login"""

    template_name = "accounts/login_social.html"

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase:
        if not settings.GOOGLE_OAUTH_CLIENT_ID:
            next_parameter = request.GET.get(REDIRECT_FIELD_NAME)
            url = reverse('accounts:login-native')

            if next_parameter:
                url = f"{url}?{REDIRECT_FIELD_NAME}={next_parameter}"

            return HttpResponseRedirect(url)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data()
        context["disable_auto_login"] = True
        next_parameter = self.request.GET.get(REDIRECT_FIELD_NAME)
        if next_parameter:
            context["next"] = next_parameter
        return context

    def post(self, request: HttpRequest):
        """Handle the sign in token"""

        redirect_to = request.GET.get(REDIRECT_FIELD_NAME, "/")
        credential = request.POST["credential"]
        id_info = id_token.verify_oauth2_token(credential, requests.Request(), settings.GOOGLE_OAUTH_CLIENT_ID)

        first_name = id_info["given_name"]
        last_name = id_info["family_name"]
        email = id_info["email"]

        if not _hosted_domain_allowed(id_info):
            if request.POST.get("from_auto"):
                request.session[USER_DID_LOGOUT_KEY] = True
                return HttpResponseRedirect(redirect_to)

            if len(allowed_domains) == 1:
                msg = _("Login is only allowed from ")
                msg += allowed_domains[0]
            else:
                msg = _("Login is only allowed from one of the following domains: ")
                msg += ", ".join(allowed_domains)
                msg += " " + _("domains")

            messages.add_message(request, messages.ERROR, msg)

            return HttpResponseRedirect(request.get_full_path())

        try:
            #  pylint: disable=invalid-name
            user = UserModel.objects.get(email=email)

            if not user.is_active:
                return JsonResponse({
                    'success': False,
                    'error': _('Your account is not currently active',)
                })

        except UserModel.DoesNotExist:
            user = UserModel(email=email)

        attr_map = {
            'first_name': first_name,
            'last_name': last_name,
        }

        do_save = False
        if not user.pk:
            do_save = True

        for attr_name, desired_value in attr_map.items():
            current_value = getattr(user, attr_name)
            if current_value != desired_value:
                setattr(user, attr_name, desired_value)
                do_save = True

        if do_save:
            user.save()

        login(request, user)
        request.session[USER_DID_LOGOUT_KEY] = False
        return HttpResponseRedirect(redirect_to)


class NativeLoginView(LoginView):
    """Our login view"""

    template_name = "accounts/login_native.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context['disable_auto_login'] = True
        return context


def logout(request: HttpRequest):
    """Log out the user and flag their session to not log back in quickly"""

    next_url = request.GET.get(REDIRECT_FIELD_NAME, "/")
    auth_logout(request)
    request.session[USER_DID_LOGOUT_KEY] = True
    return HttpResponseRedirect(next_url)


def reset_session(request: HttpRequest):
    """Clear the user's session"""

    next_url = request.GET.get(REDIRECT_FIELD_NAME, "/")
    request.session.flush()
    return HttpResponseRedirect(next_url)


def _hosted_domain_allowed(id_info: dict) -> bool:
    email = id_info["email"]

    hosted_domain = id_info.get("hd", "").lower()

    if not allowed_domains:
        return True

    if hosted_domain in allowed_domains:
        return True

    if bypass_hd_check_on_existing_email:
        if UserModel.objects.filter(email=email).exists():
            log.info("Bypassing hosted domain rejection due to existing email",
                     email=email, hosted_domain=hosted_domain,
                     allowed_domains=allowed_domains)
            return True

    log.info("Rejecting Google login hosted domain checked login", email=email,
             hosted_domain=hosted_domain, allowed_domains=allowed_domains)
    return False
