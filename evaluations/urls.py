"""URLs for evaluations"""

from django.urls import path

from . import views

#  pylint: disable=invalid-name
app_name = "evaluations"
urlpatterns = [
    path("", views.EvaluationList.as_view(), name="index"),
    path("complete/<int:pk>/", views.CompleteEvaluation.as_view(), name="complete"),
]
