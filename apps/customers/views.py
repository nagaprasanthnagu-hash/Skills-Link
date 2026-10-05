from django.views.generic import TemplateView

from apps.core.mixins import RoleRequiredMixin


class CustomerDashboardView(RoleRequiredMixin, TemplateView):
    allowed_roles = ['customer']
    template_name = 'customers/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.bookings.models import Booking
        from apps.categories.models import ServiceCategory

        customer_profile = self.request.user.customer_profile
        bookings = Booking.objects.filter(customer=customer_profile).select_related(
            'provider__user', 'category',
        ).order_by('-created_at')

        context['recent_bookings'] = bookings[:5]
        context['total_bookings'] = bookings.count()
        context['active_bookings'] = bookings.filter(status__in=['pending', 'accepted', 'in_progress']).count()
        context['completed_bookings'] = bookings.filter(status='completed').count()
        context['completed_services'] = bookings.filter(status='completed').select_related('review')[:5]
        context['categories'] = ServiceCategory.objects.filter(is_active=True)[:8]
        return context
