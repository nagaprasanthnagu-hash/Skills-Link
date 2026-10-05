"""Development settings — DEBUG=True, SQLite, console email backend."""
from .base import *  # noqa: F401,F403
from .base import BASE_DIR, env

DEBUG = True

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Email backend — defaults to console (OTP emails print to this terminal)
# so the academic demo keeps working with zero configuration. If real SMTP
# credentials are supplied via .env (see .env.example), switch to sending
# real email instead — same env vars production.py uses, so no new pattern
# is introduced. EMAIL_BACKEND itself can also be overridden directly.
EMAIL_BACKEND = env('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
if env('EMAIL_HOST'):
    EMAIL_BACKEND = env('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
    EMAIL_HOST = env('EMAIL_HOST', '')
    EMAIL_PORT = int(env('EMAIL_PORT', '587'))
    EMAIL_HOST_USER = env('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', '')
    EMAIL_USE_TLS = env('EMAIL_USE_TLS', 'True') == 'True'

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Termux on Android (running the dev server from shared storage, e.g.
# /storage/emulated/0/...) does not implement fcntl.flock(), which
# Django's FileSystemStorage._save() always calls to guard concurrent
# writes during file upload. That raises:
#   OSError: [Errno 38] Function not implemented
# on every image upload (provider profile photos, work photos) when the
# project lives on that kind of storage. Django has no built-in setting
# to turn this off, so we no-op the two lock functions it calls —
# development only, a single local dev server has no concurrent writers
# to protect against anyway. Production keeps Django's real file locking.
try:
    from django.core.files import locks as _django_file_locks

    def _noop_lock(f, flags):
        return True

    def _noop_unlock(f):
        return True

    _django_file_locks.lock = _noop_lock
    _django_file_locks.unlock = _noop_unlock
except ImportError:
    pass
