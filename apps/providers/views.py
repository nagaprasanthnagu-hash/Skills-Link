from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import TemplateView

from apps.core.mixins import RoleRequiredMixin
from apps.providers.forms import ProviderProfileForm, ProviderTagForm, WorkPhotoForm


class ProviderDashboardView(RoleRequiredMixin, TemplateView):
    allowed_roles = ['provider']
    template_name = 'providers/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.bookings.models import Booking

        provider_profile = self.request.user.provider_profile
        context['provider_profile'] = provider_profile

        if provider_profile.category_id:
            pending_bookings = Booking.objects.filter(
                category=provider_profile.category, status='pending',
            ).select_related('customer__user', 'category').order_by('preferred_datetime')
        else:
            pending_bookings = Booking.objects.none()

        active_bookings = Booking.objects.filter(
            provider=provider_profile, status__in=['accepted', 'in_progress'],
        ).select_related('customer__user', 'category').order_by('preferred_datetime')

        context['pending_bookings'] = pending_bookings[:10]
        context['active_bookings'] = active_bookings
        context['completed_bookings'] = Booking.objects.filter(
            provider=provider_profile, status='completed',
        ).select_related('customer__user', 'category').prefetch_related('work_photos').order_by('-preferred_datetime')[:10]
        context['completed_count'] = Booking.objects.filter(provider=provider_profile, status='completed').count()
        context['average_rating'] = provider_profile.average_rating
        context['review_count'] = provider_profile.review_count
        context['profile_incomplete'] = provider_profile.category_id is None
        return context


class ProviderProfileSetupView(RoleRequiredMixin, View):
    allowed_roles = ['provider']
    template_name = 'providers/profile_form.html'

    def get(self, request):
        form = ProviderProfileForm(instance=request.user.provider_profile)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = ProviderProfileForm(
            request.POST, request.FILES, instance=request.user.provider_profile,
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Provider profile saved successfully.')
            return redirect('providers:dashboard')
        return render(request, self.template_name, {'form': form})


class ProviderTagListView(RoleRequiredMixin, View):
    """'Specialized Services' tag management (Section 6): a provider views
    their own tags and adds a new one from the same page. Always scoped to
    request.user.provider_profile — never to any pk supplied by the client."""
    allowed_roles = ['provider']
    template_name = 'providers/tags.html'

    def _context(self, request, form=None):
        return {
            'tags': request.user.provider_profile.service_tags.all(),
            'form': form or ProviderTagForm(provider=request.user.provider_profile),
        }

    def get(self, request):
        return render(request, self.template_name, self._context(request))

    def post(self, request):
        form = ProviderTagForm(request.POST, provider=request.user.provider_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Service tag added.')
            return redirect('providers:tags')
        return render(request, self.template_name, self._context(request, form))


class ProviderTagEditView(RoleRequiredMixin, View):
    """Edit one of the current provider's own tags. The tag is always looked
    up filtered by provider=request.user.provider_profile (Section 7) — a
    provider can never load or save another provider's tag by guessing a
    different pk in the URL."""
    allowed_roles = ['provider']
    template_name = 'providers/tag_edit.html'

    def _get_tag(self, request, pk):
        from apps.providers.models import ProviderTag
        return get_object_or_404(ProviderTag, pk=pk, provider=request.user.provider_profile)

    def get(self, request, pk):
        tag = self._get_tag(request, pk)
        form = ProviderTagForm(instance=tag, provider=request.user.provider_profile)
        return render(request, self.template_name, {'form': form, 'tag': tag})

    def post(self, request, pk):
        tag = self._get_tag(request, pk)
        form = ProviderTagForm(request.POST, instance=tag, provider=request.user.provider_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Service tag updated.')
            return redirect('providers:tags')
        return render(request, self.template_name, {'form': form, 'tag': tag})


def provider_tag_delete_view(request, pk):
    """Deletes one of the current provider's own tags. Mirrors the ownership
    check already used by work_photo_delete_view below: role-checked, then
    looked up scoped to request.user.provider_profile so a provider can
    never delete another provider's tag by editing the URL or POST body —
    the pk in the URL is never trusted on its own (Section 7)."""
    from apps.providers.models import ProviderTag

    if not request.user.is_authenticated or getattr(request.user, 'userprofile', None) is None or request.user.userprofile.role != 'provider':
        messages.error(request, "You don't have permission to view this page.")
        return redirect('home')

    tag = get_object_or_404(ProviderTag, pk=pk, provider=request.user.provider_profile)
    if request.method == 'POST':
        tag.delete()
        messages.success(request, 'Service tag removed.')
    return redirect('providers:tags')


class WorkPhotoUploadView(RoleRequiredMixin, View):
    """Upload one or more completed-work photos against a specific booking.
    Only the provider assigned to that booking may upload, and only once the
    booking has reached Completed (Section 2 / 9 of the work-gallery spec)."""
    allowed_roles = ['provider']
    template_name = 'providers/work_photo_upload.html'

    def _get_booking(self, request, booking_id):
        from apps.bookings.models import Booking
        return get_object_or_404(
            Booking, pk=booking_id,
            provider=request.user.provider_profile,
            status=Booking.STATUS_COMPLETED,
        )

    def get(self, request, booking_id):
        booking = self._get_booking(request, booking_id)
        photos = booking.work_photos.all()
        return render(request, self.template_name, {'form': WorkPhotoForm(), 'booking': booking, 'photos': photos})

    def post(self, request, booking_id):
        from apps.providers.models import WorkPhoto, validate_profile_photo

        booking = self._get_booking(request, booking_id)
        form = WorkPhotoForm(request.POST)
        images = request.FILES.getlist('images')

        if not images:
            messages.error(request, 'Please choose at least one photo to upload.')
        elif not form.is_valid():
            pass
        else:
            caption = form.cleaned_data['caption']
            created = 0
            for image in images:
                try:
                    validate_profile_photo(image)
                except ValidationError as exc:
                    messages.error(request, f'{image.name}: {exc.message}')
                    continue
                WorkPhoto.objects.create(
                    booking=booking, provider=request.user.provider_profile,
                    image=image, caption=caption,
                )
                created += 1
            if created:
                messages.success(request, f'{created} photo(s) uploaded.')
                return redirect('providers:work_photo_upload', booking_id=booking.pk)

        photos = booking.work_photos.all()
        return render(request, self.template_name, {'form': form, 'booking': booking, 'photos': photos})


def work_photo_delete_view(request, pk):
    from apps.providers.models import WorkPhoto

    if not request.user.is_authenticated or request.user.userprofile.role != 'provider':
        messages.error(request, "You don't have permission to view this page.")
        return redirect('home')

    photo = get_object_or_404(WorkPhoto, pk=pk, provider=request.user.provider_profile)
    booking_id = photo.booking_id
    if request.method == 'POST':
        photo.image.delete(save=False)
        photo.delete()
        messages.success(request, 'Photo removed.')
    return redirect('providers:work_photo_upload', booking_id=booking_id)
