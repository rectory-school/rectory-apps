"""URLS for the icon system"""

from django.urls import path

from . import views

#  pylint: disable=invalid-name
app_name = 'icons'
urlpatterns = [
    path('', views.PageList.as_view(), name='page-list'),
    path('set_positions/', views.set_page_positions, name="set-sort-positions"),
    path('web/<slug:slug>/', views.PageDetail.as_view(), name="page"),
]
