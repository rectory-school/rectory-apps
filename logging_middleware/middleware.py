"""Logging middleware"""

import logging
from django.utils import timezone
from ipware import get_client_ip


class LoggingMiddleware:
    """Middleware that logs all requests/responses"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.log = logging.getLogger('log-http-requests')
        self.log.info("Logging middleware inititalized")

    def __call__(self, request):
        # Pre-request
        started_at = timezone.now()
        client_ip, _ = get_client_ip(request)

        response = self.get_response(request)

        # Post-request
        finished_at = timezone.now()

        took = finished_at - started_at

        extra = {
            'remote-host': client_ip,
            'request-time': took.total_seconds(),
            'request-path': request.path,
            'request-method': request.method,
            'response-status-code': response.status_code,
            'request-host': request.get_host(),
            'request-scheme': request.scheme,
        }

        if hasattr(response, "content"):
            extra['response-size'] = len(response.content)

        if hasattr(request, 'user'):
            extra['user'] = str(request.user)

        self.log.info("%s %s %d", request.method, request.path, response.status_code, extra=extra)
        return response
