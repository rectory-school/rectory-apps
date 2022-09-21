"""URLs for enrichment system"""

from django.urls import path

from . import views

app_name = "enrichment"
urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("assign/", views.AssignView.as_view(), name="assign"),
    path("assign/all/", views.AssignAllView.as_view(), name="assign-all"),
    path("advisees/", views.AdviseeListView.as_view(), name="advisee-list"),
    path("advisors/", views.AdvisorListView.as_view(), name="advisor-list"),
    path(
        "assign/unassigned/",
        views.AssignUnassignedView.as_view(),
        name="assign-unassigned",
    ),
    path(
        "assign/student/<int:student_id>/",
        views.AssignByStudentView.as_view(),
        name="assign-student",
    ),
    path(
        "assign/for_advisor/<int:teacher_id>/",
        views.AssignForAdvisorView.as_view(),
        name="assign-for-teacher",
    ),
    path("assign/save/", views.assign, name="assign-save"),
]
