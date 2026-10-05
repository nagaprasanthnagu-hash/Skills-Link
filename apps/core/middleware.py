"""
Custom middleware (Section 82 logging strategy, Section 64 security).

RequestLoggingMiddleware logs every request's method/path/status/user at
INFO level (Section 82.2), while never logging passwords, OTPs, or other
sensitive payloads (Section 82.3).

LoginRateLimitMiddleware enforces FR security requirement "Login Rate
Limiting" by tracking failed login attempts per client IP using Django's
cache framework and temporarily blocking further attempts once the
threshold in settings.LOGIN_RATE_LIMIT_ATTEMPTS is exceeded.
"""
import logging

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.shortcuts import redirect
from django.urls import resolve

logger = logging.getLogger('apps.core')


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user_repr = request.user.username if getattr(request, 'user', None) and request.user.is_authenticated else 'anonymous'
        logger.info('%s %s -> %s (user=%s)', request.method, request.path, response.status_code, user_repr)
        return response


class NoStoreForAuthenticatedMiddleware:
    """
    Marks every response served to an authenticated user as non-cacheable
    (Section 5: "prevent browser back-navigation from exposing protected
    pages where practical"). Without this, pressing Back after Logout can
    briefly show a browser-cached copy of a page like a dashboard before
    the next real request re-checks the (now-cleared) session. Applied
    uniformly here rather than per-view, matching the existing pattern of
    centralising cross-cutting auth concerns in middleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if getattr(request, 'user', None) and request.user.is_authenticated:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
        return response


def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


class LoginRateLimitMiddleware:
    """
    Blocks further login POSTs from a client IP once
    LOGIN_RATE_LIMIT_ATTEMPTS failed attempts occur within
    LOGIN_RATE_LIMIT_WINDOW_SECONDS. The accounts LoginView records failures
    via `record_failed_login`; this middleware only enforces the block.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            match = resolve(request.path)
        except Exception:
            match = None

        is_login_post = (
            request.method == 'POST'
            and match is not None
            and match.view_name == 'accounts:login'
        )

        if is_login_post:
            ip = _client_ip(request)
            cache_key = f'login_attempts:{ip}'
            attempts = cache.get(cache_key, 0)
            if attempts >= settings.LOGIN_RATE_LIMIT_ATTEMPTS:
                messages.error(
                    request,
                    'Too many failed login attempts. Please wait a few minutes before trying again.',
                )
                return redirect('accounts:login')

        return self.get_response(request)


def record_failed_login(request):
    ip = _client_ip(request)
    cache_key = f'login_attempts:{ip}'
    attempts = cache.get(cache_key, 0)
    cache.set(cache_key, attempts + 1, timeout=settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS)


def clear_failed_login(request):
    ip = _client_ip(request)
    cache.delete(f'login_attempts:{ip}')
