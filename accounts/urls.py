"""URLS for accounts"""

from django.urls import path

import django.contrib.auth.views

from . import views

#  pylint: disable=invalid-name
app_name = 'accounts'
urlpatterns = [
    path('login/', views.SocialLoginView.as_view(), name='login'),
    path('login/native/', views.NativeLoginView.as_view(), name='login-native'),
    path('logout/', django.contrib.auth.views.LogoutView.as_view(), name='logout')
]
