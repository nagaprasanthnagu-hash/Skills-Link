"""
Base settings for the Service Provided Web Application.

Shared by every environment (development, production). Environment-specific
overrides live in development.py and production.py — only
DJANGO_SETTINGS_MODULE needs to change to switch environments (Section 56.6
of the PRD).
"""
import os
from pathlib import Path

# BASE_DIR points at the project root (service_provided_webapp/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _load_dotenv(path):
    """Minimal .env loader — avoids adding a third-party dependency just
    for reading KEY=VALUE lines into os.environ."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, value = line.partition('=')
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(BASE_DIR / '.env')


def env(key, default=None):
    return os.environ.get(key, default)


SECRET_KEY = env('DJANGO_SECRET_KEY', 'django-insecure-dev-only-change-me-in-production')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # Local apps — one per module (Section 56.2)
    'apps.core',
    'apps.accounts',
    'apps.categories',
    'apps.customers',
    'apps.providers',
    'apps.bookings',
    'apps.reviews',
    'apps.dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Custom middleware (Section 82 logging strategy, Section 38 security)
    'apps.core.middleware.RequestLoggingMiddleware',
    'apps.core.middleware.LoginRateLimitMiddleware',
    'apps.core.middleware.NoStoreForAuthenticatedMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Custom context processor (Section 56.7) — injects role and
                # unread-notification counters into every template.
                'apps.core.context_processors.role_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Custom authentication backend supporting login by username OR email
# (FR-A of Section 20), falling back to Django's default ModelBackend.
AUTHENTICATION_BACKENDS = [
    'apps.accounts.backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
]

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:post_login_redirect'
LOGOUT_REDIRECT_URL = 'home'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static / media files (Section 56.4)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Messages framework -> Bootstrap 5 alert classes
from django.contrib.messages import constants as message_constants  # noqa: E402

MESSAGE_TAGS = {
    message_constants.DEBUG: 'secondary',
    message_constants.INFO: 'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR: 'danger',
}

# Session configuration (Section 64)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # 14 days when "remember me" is used
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# File upload validation (Section 62.4 — profile photo JPEG/PNG, max 2MB)
MAX_UPLOAD_SIZE_BYTES = 2 * 1024 * 1024
ALLOWED_UPLOAD_IMAGE_TYPES = ['image/jpeg', 'image/png']

# Login rate limiting (Section 64)
LOGIN_RATE_LIMIT_ATTEMPTS = 5
LOGIN_RATE_LIMIT_WINDOW_SECONDS = 300  # 5 minutes

# Email backend — overridden per environment. OTP emails print to console
# in development so the academic demo works without a real mail server.
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', 'no-reply@serviceprovided.local')
OTP_VALIDITY_MINUTES = 10

# Logging (Section 82)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'app.log',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 3,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
os.makedirs(BASE_DIR / 'logs', exist_ok=True)
