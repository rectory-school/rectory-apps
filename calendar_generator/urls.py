"""URLs for calendar"""

from django.urls import path

from . import views

#  pylint: disable=invalid-name
app_name = 'calendar_generator'
urlpatterns = [
    path('', views.Calendars.as_view(), name='calendar-list'),
    path('<int:pk>/', views.Calendar.as_view(), name='calendar'),

    path('calendar-<int:calendar_id>/pdf/style-<int:style_index>/size-<int:layout_index>/all_months/',
         views.PDFMonths.as_view(),
         name='months-pdf'),

    path('calendar-<int:calendar_id>/pdf/style-<int:style_index>/size-<int:layout_index>/one-page/',
         views.PDFOnePage.as_view(),
         name='one-page-pdf'),

    path('calendar-<int:calendar_id>/custom/', views.custom_preview, name='custom'),
    path('calendar-<int:calendar_id>/pdf/single-grid/', views.pdf_single_grid, name='pdf-single-grid'),
]
