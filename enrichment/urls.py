"""URLs for enrichment system"""

from django.urls import path

from . import views

app_name = "enrichment"
urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("assign/", views.AssignView.as_view(), name="assign"),
    path("assign/all/", views.AssignAllView.as_view(), name="assign-all"),
    path(
        "assign/unassigned/",
        views.AssignUnassignedView.as_view(),
        name="assign-unassigned",
    ),
    path("assign/save/", views.assign, name="assign-save"),
]
