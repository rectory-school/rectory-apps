"""URLs for calendar"""

from django.urls import path

from . import views

#  pylint: disable=invalid-name
app_name = "calendar_generator"
urlpatterns = [
    path("", views.Calendars.as_view(), name="calendar-list"),
    path("<int:pk>/", views.Calendar.as_view(), name="calendar"),
    path("calendar/<int:calendar_id>/custom/", views.custom_preview, name="custom"),
    path(
        "calendar/<int:calendar_id>/pdf/single-grid/colors/<int:color_set_id>/layout/<int:layout_id>/from/<int:start_year>-<int:start_month>-<int:start_day>/to/<int:end_year>-<int:end_month>-<int:end_day>/",
        views.pdf_single_grid,
        name="pdf-single-grid",
    ),
    path(
        "calendar/<int:calendar_id>/pdf/all-months/colors/<int:color_set_id>/layout/<int:layout_id>/",
        views.pdf_all_months,
        name="months-pdf",
    ),
    path(
        "calendar/<int:calendar_id>/pdf/one-page/colors/<int:color_set_id>/layout/<int:layout_id>/",
        views.pdf_one_page,
        name="one-page-pdf",
    ),
]
