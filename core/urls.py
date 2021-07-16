"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

import accounts.urls
import accounts.views

import calendar_generator.urls


urlpatterns = [
    path('', TemplateView.as_view(template_name="home.html")),
    path('accounts/', include(accounts.urls)),

    # I want admin to use my login page - intercept it's call
    path('admin/login/', accounts.views.SocialLoginView.as_view()),
    path('admin/', admin.site.urls),

    path('calendars/', include(calendar_generator.urls))
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns.append(path('__debug__/', include(debug_toolbar.urls)))
