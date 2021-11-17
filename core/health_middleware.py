"""Basic health check middleware that bypasses the allowed_hosts check"""

from django.conf import settings
from django.http import HttpResponse


class HealthCheckMiddleware:
    """Health check middleware can bypass the allowed hosts check"""

    # The allowed hosts check, at least on DigitalOcean,
    # doesn't include a host header. This is a quick fix.
    def __init__(self, get_response):
        self.get_response = get_response

        try:
            self.url = settings.HEALTH_CHECK_URL
        except AttributeError:
            self.url = None

    def __call__(self, request):
        if self.url and request.path == self.url:
            return HttpResponse('ok')
        return self.get_response(request)