"""Role-check decorator for function-based views (Section 65.1 — FBVs are
acceptable for simple, single-purpose actions such as accept/cancel)."""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from apps.core.mixins import dashboard_url_for_role


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url='accounts:login')
        def _wrapped(request, *args, **kwargs):
            profile = getattr(request.user, 'userprofile', None)
            role = profile.role if profile else None
            if role not in roles:
                messages.error(request, "You don't have permission to view this page.")
                return redirect(dashboard_url_for_role(role))
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
