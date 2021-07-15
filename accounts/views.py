"""Accounts views"""

import django.contrib.auth.views


class LoginView(django.contrib.auth.views.LoginView):
    """Our login view"""
    template_name = "accounts/login.html"


class LogoutView(django.contrib.auth.views.LogoutView):
    """Our log out view"""
    template_name = "accounts/logout.html"
