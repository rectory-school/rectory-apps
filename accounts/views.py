"""Accounts views"""

from typing import Dict, Any
from datetime import timedelta

import structlog

from google.oauth2 import id_token
from google.auth.transport import requests

from django.http.response import HttpResponseRedirect, HttpResponseBase
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.views import LoginView
from django.contrib.auth import REDIRECT_FIELD_NAME, logout as auth_logout
from django.views.generic import TemplateView, FormView
from django.contrib.auth import get_user_model, login
from django.http import JsonResponse
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django import forms
from django.forms import ValidationError
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.db import transaction

from . import models

log = structlog.get_logger()

UserModel = get_user_model()

LOGIN_REDIRECT_URL = settings.LOGIN_REDIRECT_URL
USER_DID_LOGOUT_KEY = "user_did_logout"

allowed_domains = [domain.lower() for domain in settings.GOOGLE_HOSTED_DOMAINS]


class SocialLoginView(TemplateView):
    """Handle social login"""

    template_name = "accounts/login_social.html"

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        if not settings.GOOGLE_OAUTH_CLIENT_ID:
            next_parameter = request.GET.get(REDIRECT_FIELD_NAME)
            url = reverse("accounts:login-native")

            if next_parameter:
                url = f"{url}?{REDIRECT_FIELD_NAME}={next_parameter}"

            return HttpResponseRedirect(url)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data()
        context["disable_auto_login"] = True
        next_parameter = self.request.GET.get(REDIRECT_FIELD_NAME)
        cfg: models.LoginConfiguration = models.LoginConfiguration.get_solo()

        if next_parameter:
            context["next"] = next_parameter

        context["show_google_login"] = cfg.enable_google_login
        context["show_email_login"] = cfg.enable_email_login

        return context

    def post(self, request: HttpRequest):
        """Handle the sign in token"""

        cfg: models.LoginConfiguration = models.LoginConfiguration.get_solo()
        if not cfg.enable_google_login:
            messages.error(request, "Google login is not enabled")
            return HttpResponseRedirect("accounts:login")

        redirect_to = request.GET.get(REDIRECT_FIELD_NAME, "/")
        credential = request.POST["credential"]
        id_info = id_token.verify_oauth2_token(
            credential, requests.Request(), settings.GOOGLE_OAUTH_CLIENT_ID
        )

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
                return JsonResponse(
                    {
                        "success": False,
                        "error": _(
                            "Your account is not currently active",
                        ),
                    }
                )

        except UserModel.DoesNotExist:
            user = UserModel(email=email)

        attr_map = {
            "first_name": first_name,
            "last_name": last_name,
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

        context["disable_auto_login"] = True
        return context


class EmailLoginForm(forms.Form):
    email_address = forms.EmailField()

    def clean_email_address(self):
        address = self.cleaned_data["email_address"]
        if user := UserModel.objects.filter(email=address).first():
            self.user = user
            return address

        raise ValidationError("That e-mail address is invalid")


class EmailLoginView(FormView):
    template_name = "accounts/login_email.html"
    form_class = EmailLoginForm
    success_url = reverse_lazy("accounts:login-email")

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        cfg: models.LoginConfiguration = models.LoginConfiguration.get_solo()

        if not cfg.enable_email_login:
            messages.warning(
                request,
                "E-mail login is not enabled. Please log in with another method.",
            )
            return HttpResponseRedirect(reverse("accounts:login"))

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: EmailLoginForm) -> HttpResponse:
        user: UserModel = form.user
        next_url = self.request.GET.get(REDIRECT_FIELD_NAME)

        obj = models.TemporaryLoginCode.objects.create(
            user=user, expiration=timezone.now() + timedelta(hours=1)
        )

        login_url = reverse("accounts:login-email", kwargs={"code": obj.code})
        if next_url:
            login_url = login_url + f"?{REDIRECT_FIELD_NAME}={next_url}"

        login_url = f"{settings.EMAIL_BASE_URL}{login_url}"

        msg = render_to_string(
            "accounts/email_login_message.txt",
            {"login_url": login_url},
        )

        send_mail(
            "Rectory Apps Login",
            msg,
            from_email=None,
            recipient_list=[user.email],
        )

        messages.info(
            self.request,
            "A login link has been sent to your e-mail address. Please click it to log in.",
        )

        return HttpResponseRedirect(self.get_success_url())


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


def code_login(request: HttpRequest, code: str):
    """Log the user in based on an e-mail code"""

    next_url = request.GET.get(REDIRECT_FIELD_NAME)
    login_url = reverse("accounts:login-email")

    if next_url:
        login_url = f"{login_url}?{REDIRECT_FIELD_NAME}={next_url}"

    cfg: models.LoginConfiguration = models.LoginConfiguration.get_solo()

    if not cfg.enable_email_login:
        messages.warning(
            request, "E-mail login is not enabled. Please log in with another method."
        )
        return HttpResponseRedirect(login_url)

    with transaction.atomic():
        obj = (
            models.TemporaryLoginCode.objects.filter(
                code=code,
                used_at__isnull=True,
                expiration__gte=timezone.now(),
            )
            .select_for_update()
            .first()
        )

        if not obj:
            messages.warning(
                request,
                "The e-mail link you used was not valid. Please request a new code or use an alternate login method.",
            )

            return HttpResponseRedirect(login_url)

        obj.used_at = timezone.now()
        obj.save()

    login(request, obj.user)

    if next_url:
        return HttpResponseRedirect(next_url)

    return HttpResponseRedirect(reverse("home"))


def _hosted_domain_allowed(id_info: dict) -> bool:
    email = id_info["email"]

    hosted_domain = id_info.get("hd", "").lower()

    if not allowed_domains:
        return True

    if hosted_domain in allowed_domains:
        return True

    if UserModel.objects.filter(email=email, allow_google_hd_bypass=True).exists():
        log.info(
            "Bypassing hosted domain rejection due to existing email",
            email=email,
            hosted_domain=hosted_domain,
            allowed_domains=allowed_domains,
        )
        return True

    log.info(
        "Rejecting Google login hosted domain checked login",
        email=email,
        hosted_domain=hosted_domain,
        allowed_domains=allowed_domains,
    )
    return False
