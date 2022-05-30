"""URLS for accounts"""

from django.urls import path

from . import views

#  pylint: disable=invalid-name
app_name = "accounts"
urlpatterns = [
    path("login/", views.SocialLoginView.as_view(), name="login"),
    path("login/native/", views.NativeLoginView.as_view(), name="login-native"),
    path("logout/", views.logout, name="logout"),
    path("reset-session/", views.reset_session, name="reset-session"),
]
