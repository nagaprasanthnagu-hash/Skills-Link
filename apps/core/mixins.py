"""
Reusable access-control mixins (Section 56.7 of the PRD).

RoleRequiredMixin centralises role-based access control so the same check
is not re-implemented per view across accounts, customers, providers,
bookings, reviews, and dashboard.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


class RoleRequiredMixin(LoginRequiredMixin):
    """
    Restrict a class-based view to one or more roles.

    Usage:
        class SomeView(RoleRequiredMixin, View):
            allowed_roles = ['customer']
    """
    allowed_roles = []
    permission_denied_message = "You don't have permission to view this page."

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        profile = getattr(request.user, 'userprofile', None)
        role = profile.role if profile else None

        if self.allowed_roles and role not in self.allowed_roles:
            messages.error(request, self.permission_denied_message)
            return redirect(self._dashboard_url_for(role))

        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def _dashboard_url_for(role):
        return {
            'customer': 'customers:dashboard',
            'provider': 'providers:dashboard',
            'admin': 'dashboard:index',
        }.get(role, 'home')


def dashboard_url_for_role(role):
    return RoleRequiredMixin._dashboard_url_for(role)
