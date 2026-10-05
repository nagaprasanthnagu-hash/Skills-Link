from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView

from apps.bookings import services
from apps.bookings.forms import BookingForm
from apps.bookings.models import Booking, BookingStatusLog
from apps.core.decorators import role_required
from apps.core.mixins import RoleRequiredMixin


class BookingCreateView(RoleRequiredMixin, View):
    allowed_roles = ['customer']
    template_name = 'bookings/booking_form.html'

    def get(self, request):
        form = BookingForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = services.create_booking(
                customer_profile=request.user.customer_profile,
                category=form.cleaned_data['category'],
                preferred_datetime=form.cleaned_data['preferred_datetime'],
                address=form.cleaned_data['address'],
                description=form.cleaned_data['description'],
            )
            messages.success(request, f'Booking #{booking.id} created. We\u2019ll notify you once a provider accepts it.')
            return redirect('bookings:detail', pk=booking.pk)
        return render(request, self.template_name, {'form': form})


class BookingHistoryView(RoleRequiredMixin, View):
    allowed_roles = ['customer', 'provider']
    template_name = 'bookings/history.html'

    def get(self, request):
        profile = request.user.userprofile
        if profile.role == 'customer':
            queryset = Booking.objects.filter(customer=request.user.customer_profile)
        else:
            queryset = Booking.objects.filter(provider=request.user.provider_profile)

        status_filter = request.GET.get('status')
        if status_filter in dict(Booking.STATUS_CHOICES):
            queryset = queryset.filter(status=status_filter)

        queryset = queryset.select_related('customer__user', 'provider__user', 'category').order_by('-created_at')
        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(request.GET.get('page'))

        return render(request, self.template_name, {
            'page_obj': page_obj,
            'status_choices': Booking.STATUS_CHOICES,
            'selected_status': status_filter,
        })


class BookingDetailView(RoleRequiredMixin, DetailView):
    allowed_roles = ['customer', 'provider', 'admin']
    model = Booking
    template_name = 'bookings/detail.html'
    context_object_name = 'booking'

    def get_queryset(self):
        return Booking.objects.select_related('customer__user', 'provider__user', 'category')

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        booking = self.object
        profile = request.user.userprofile

        is_owner = profile.role == 'customer' and booking.customer_id == request.user.customer_profile.id
        is_assigned_provider = profile.role == 'provider' and booking.provider_id == getattr(request.user.provider_profile, 'id', None)
        is_admin = profile.role == 'admin'
        # A provider who has not accepted yet is never "assigned" — but they
        # still need to reach this page to see the Accept action. Without this,
        # a same-category provider is blocked from viewing (and therefore from
        # ever accepting) any booking that isn't already theirs.
        can_accept = (
            profile.role == 'provider' and booking.status == Booking.STATUS_PENDING
            and getattr(request.user.provider_profile, 'category_id', None) == booking.category_id
        )

        if not (is_owner or is_assigned_provider or can_accept or is_admin):
            messages.error(request, "You don't have permission to view this page.")
            from apps.core.mixins import dashboard_url_for_role
            return redirect(dashboard_url_for_role(profile.role))

        context = self.get_context_data(object=booking)
        context['status_logs'] = booking.status_logs.all()
        context['can_cancel'] = is_owner and booking.is_cancellable
        context['can_accept'] = can_accept
        context['can_advance'] = is_assigned_provider and booking.status in [Booking.STATUS_ACCEPTED, Booking.STATUS_IN_PROGRESS]
        context['can_review'] = is_owner and booking.status == Booking.STATUS_COMPLETED and not booking.has_review
        return self.render_to_response(context)


@role_required('customer')
def booking_cancel_view(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    try:
        services.cancel_booking(booking, request.user.customer_profile)
        messages.success(request, f'Booking #{booking.id} cancelled.')
    except PermissionDenied:
        messages.error(request, "You don't have permission to view this page.")
    except services.InvalidTransitionError:
        messages.error(request, 'This action is no longer available for this booking.')
    return redirect('bookings:detail', pk=pk)


@role_required('provider')
def booking_accept_view(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    try:
        services.accept_booking(booking, request.user.provider_profile)
        messages.success(request, f'Booking #{booking.id} accepted.')
    except PermissionDenied as exc:
        messages.error(request, str(exc))
    except services.InvalidTransitionError as exc:
        messages.error(request, str(exc))
    return redirect('bookings:detail', pk=pk)


@role_required('provider')
def booking_status_update_view(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    new_status = request.POST.get('new_status')
    try:
        services.advance_status(booking, request.user.provider_profile, new_status)
        messages.success(request, f'Booking #{booking.id} marked as {booking.get_status_display()}.')
    except PermissionDenied as exc:
        messages.error(request, str(exc))
    except services.InvalidTransitionError as exc:
        messages.error(request, 'This action is no longer available for this booking.')
    return redirect('bookings:detail', pk=pk)


class NotificationListView(RoleRequiredMixin, View):
    allowed_roles = ['customer', 'provider']
    template_name = 'bookings/notifications.html'

    def get(self, request):
        profile = request.user.userprofile
        if profile.role == 'customer':
            booking_ids = Booking.objects.filter(customer=request.user.customer_profile).values_list('id', flat=True)
        else:
            booking_ids = Booking.objects.filter(provider=request.user.provider_profile).values_list('id', flat=True)

        logs = BookingStatusLog.objects.filter(booking_id__in=booking_ids).select_related(
            'booking__category',
        ).order_by('-changed_at')[:30]

        return render(request, self.template_name, {'logs': logs})
