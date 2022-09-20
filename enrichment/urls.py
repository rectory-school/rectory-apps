"""URLs for enrichment system"""

from django.urls import path

from . import views

app_name = "enrichment"
urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("assign/", views.AdvisorView.as_view(), name="advisor-assign"),
    path("assign/save/", views.assign, name="advisor-assign-save"),
]
