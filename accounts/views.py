"""Accounts views"""

from typing import Dict, Any


from google.oauth2 import id_token
from google.auth.transport import requests

from django.http.response import HttpResponseBadRequest, HttpResponseRedirect, HttpResponseBase
from django.http import HttpRequest
from django.contrib.auth.views import LoginView
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.views.generic import TemplateView
from django.contrib.auth import get_user_model, login
from django.http import JsonResponse
from django.urls import reverse

from django.conf import settings

LOGIN_REDIRECT_URL = settings.LOGIN_REDIRECT_URL


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
        context = super().get_context_data(**kwargs)

        context["auth_data"] = {
            'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
            'hosted_domain': settings.GOOGLE_HOSTED_DOMAIN,
        }

        if REDIRECT_FIELD_NAME in self.request.GET:
            context[REDIRECT_FIELD_NAME] = self.request.GET[REDIRECT_FIELD_NAME]
        else:
            context[REDIRECT_FIELD_NAME] = LOGIN_REDIRECT_URL

        context["redirect_field_name"] = REDIRECT_FIELD_NAME

        return context

    def post(self, request):
        """Handle the sign in token"""

        token = request.POST["token"]
        id_info = id_token.verify_oauth2_token(token, requests.Request(), settings.GOOGLE_OAUTH_CLIENT_ID)

        first_name = id_info["given_name"]
        last_name = id_info["family_name"]
        email = id_info["email"]

        if settings.GOOGLE_HOSTED_DOMAIN:
            if id_info["hd"] != settings.GOOGLE_HOSTED_DOMAIN:
                return HttpResponseBadRequest()

        try:
            #  pylint: disable=invalid-name
            UserModel = get_user_model()
            user = UserModel.objects.get(email=email)

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

        # The JS can handle the rest
        return JsonResponse({})


class NativeLoginView(LoginView):
    """Our login view"""

    template_name = "accounts/login_native.html"
