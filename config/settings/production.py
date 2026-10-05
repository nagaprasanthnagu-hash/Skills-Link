"""
Production settings — DEBUG=False, secrets from environment variables,
security flags enabled (Section 46.2 / Section 56.6 of the PRD).

SQLite remains the default DATABASES entry for a like-for-like academic
demo deployment; swap the ENGINE/NAME/USER/PASSWORD/HOST/PORT block below
for PostgreSQL or MySQL when moving to a real production environment,
per Section 46.2's reference design.
"""
from .base import *  # noqa: F401,F403
from .base import BASE_DIR, env

DEBUG = False

ALLOWED_HOSTS = [h.strip() for h in env('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]

SECRET_KEY = env('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError('DJANGO_SECRET_KEY must be set in the production environment.')

DATABASES = {
    'default': {
        'ENGINE': env('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': env('DB_NAME', str(BASE_DIR / 'db.sqlite3')),
        'USER': env('DB_USER', ''),
        'PASSWORD': env('DB_PASSWORD', ''),
        'HOST': env('DB_HOST', ''),
        'PORT': env('DB_PORT', ''),
    }
}

EMAIL_BACKEND = env('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', '')
EMAIL_PORT = int(env('EMAIL_PORT', '587'))
EMAIL_HOST_USER = env('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = env('EMAIL_USE_TLS', 'True') == 'True'

# Security hardening (Section 64)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = env('DJANGO_SECURE_SSL_REDIRECT', 'True') == 'True'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
