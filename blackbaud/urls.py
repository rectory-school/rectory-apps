"""URLs for Blackbaud utilities"""

from django.urls import path

from . import views

#  pylint: disable=invalid-name
app_name = "blackbaud"
urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("reports/advisors/", views.AdviseeReport.as_view(), name="report-advisors"),
]
