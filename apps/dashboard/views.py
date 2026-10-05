from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import TemplateView

from apps.accounts.models import UserProfile
from apps.bookings.models import Booking
from apps.categories.models import ServiceCategory
from apps.core.mixins import RoleRequiredMixin
from apps.customers.models import CustomerProfile
from apps.providers.models import ProviderProfile


class AdminDashboardView(RoleRequiredMixin, TemplateView):
    allowed_roles = ['admin']
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_customers'] = CustomerProfile.objects.count()
        context['total_providers'] = ProviderProfile.objects.count()
        context['total_categories'] = ServiceCategory.objects.filter(is_active=True).count()
        context['total_bookings'] = Booking.objects.count()

        status_counts = {}
        for status_value, status_label in Booking.STATUS_CHOICES:
            status_counts[status_label] = Booking.objects.filter(status=status_value).count()
        context['status_counts'] = status_counts

        context['recent_bookings'] = Booking.objects.select_related(
            'customer__user', 'provider__user', 'category',
        ).order_by('-created_at')[:10]
        return context


class UserManagementView(RoleRequiredMixin, View):
    allowed_roles = ['admin']
    template_name = 'dashboard/users.html'

    def get(self, request):
        profiles = UserProfile.objects.select_related('user').filter(
            role__in=[UserProfile.ROLE_CUSTOMER, UserProfile.ROLE_PROVIDER],
        ).order_by('role', 'full_name')
        paginator = Paginator(profiles, 20)
        page_obj = paginator.get_page(request.GET.get('page'))
        return render(request, self.template_name, {'page_obj': page_obj})

    def post(self, request):
        user_id = request.POST.get('user_id')
        user = get_object_or_404(User, pk=user_id)
        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])
        state = 'activated' if user.is_active else 'deactivated'
        messages.success(request, f'Account "{user.username}" {state}.')
        return redirect('dashboard:users')


class ProviderManagementView(RoleRequiredMixin, View):
    allowed_roles = ['admin']
    template_name = 'dashboard/providers.html'

    def get(self, request):
        providers = ProviderProfile.objects.select_related('user', 'category').order_by('user__username')
        paginator = Paginator(providers, 20)
        page_obj = paginator.get_page(request.GET.get('page'))
        return render(request, self.template_name, {'page_obj': page_obj})

    def post(self, request):
        provider_id = request.POST.get('provider_id')
        provider = get_object_or_404(ProviderProfile, pk=provider_id)
        provider.is_active = not provider.is_active
        provider.save(update_fields=['is_active'])
        state = 'activated' if provider.is_active else 'deactivated'
        messages.success(request, f'Provider "{provider.user.username}" {state}.')
        return redirect('dashboard:providers')
