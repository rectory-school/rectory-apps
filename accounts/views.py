"""Accounts views"""

from typing import Dict, Any

from google.oauth2 import id_token
from google.auth.transport import requests

from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView
from django.contrib.auth import get_user_model, login
from django.http import JsonResponse

from django.conf import settings


class SocialLoginView(TemplateView):
    """Handle social login"""

    template_name = "accounts/login.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["google_oauth_client_id"] = settings.GOOGLE_OAUTH_CLIENT_ID
        context["google_hosted_domain"] = settings.GOOGLE_HOSTED_DOMAIN
        if "next" in self.request.GET:
            context["next"] = self.request.GET["next"]

        return context

    def post(self, request):
        """Handle the sign in token"""

        token = request.POST["token"]
        id_info = id_token.verify_oauth2_token(token, requests.Request(), settings.GOOGLE_OAUTH_CLIENT_ID)

        first_name = id_info["given_name"]
        last_name = id_info["family_name"]
        email = id_info["email"]

        try:
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
