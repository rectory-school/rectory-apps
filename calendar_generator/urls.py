"""URLs for calendar"""

from django.urls import path

from . import views

#  pylint: disable=invalid-name
app_name = 'calendar_generator'
urlpatterns = [
    path('', views.Calendars.as_view(), name='calendar-list'),
    path('<int:pk>/', views.Calendar.as_view(), name='calendar'),
    path('<int:calendar_id>/pdf/<int:year>/<int:month>/', views.PDFMonth.as_view(), name='month-pdf'),
    path('<int:calendar_id>/pdf/<str:preset_slug>/<int:year>/<int:month>/', views.PDFMonth.as_view(), name='month-pdf'),
]
