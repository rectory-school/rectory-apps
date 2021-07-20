"""URLS for the icon system"""

from django.urls import path

from . import views

#  pylint: disable=invalid-name
app_name = 'icons'
urlpatterns = [
    path('<slug:slug>/', views.PageDetail.as_view(), name="static-page"),
]
