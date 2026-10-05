from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView

from apps.bookings.models import Booking
from apps.core.mixins import RoleRequiredMixin
from apps.providers.models import ProviderProfile
from apps.reviews.forms import ReviewForm
from apps.reviews.models import Review


class ReviewCreateView(RoleRequiredMixin, View):
    allowed_roles = ['customer']
    template_name = 'reviews/review_form.html'

    def _get_booking(self, request, booking_id):
        return get_object_or_404(
            Booking, pk=booking_id, customer=request.user.customer_profile, status=Booking.STATUS_COMPLETED,
        )

    def get(self, request, booking_id):
        booking = self._get_booking(request, booking_id)
        if booking.has_review:
            messages.error(request, 'This booking cannot be reviewed.')
            return redirect('bookings:detail', pk=booking.pk)
        return render(request, self.template_name, {'form': ReviewForm(), 'booking': booking})

    def post(self, request, booking_id):
        booking = self._get_booking(request, booking_id)
        if booking.has_review:
            messages.error(request, 'This booking cannot be reviewed.')
            return redirect('bookings:detail', pk=booking.pk)

        form = ReviewForm(request.POST)
        if form.is_valid():
            Review.objects.create(
                booking=booking,
                customer=booking.customer,
                provider=booking.provider,
                rating=form.cleaned_data['rating'],
                comment=form.cleaned_data['comment'],
            )
            messages.success(request, 'Thank you — your review has been submitted.')
            return redirect('bookings:detail', pk=booking.pk)
        return render(request, self.template_name, {'form': form, 'booking': booking})


class ProviderReviewListView(ListView):
    model = Review
    template_name = 'reviews/provider_reviews.html'
    context_object_name = 'reviews'
    paginate_by = 10

    def get_queryset(self):
        self.provider = get_object_or_404(ProviderProfile, pk=self.kwargs['provider_id'])
        return Review.objects.filter(provider=self.provider).select_related('customer__user').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['provider'] = self.provider
        context['work_photos'] = self.provider.work_photos.select_related('booking__category')[:12]
        return context
