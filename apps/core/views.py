from django.db.models import Avg, Count, Q
from django.shortcuts import render
from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.categories.models import ServiceCategory
        from apps.providers.models import ProviderProfile

        categories = ServiceCategory.objects.filter(is_active=True)[:6].annotate(
            provider_count=Count('providers', filter=Q(providers__is_active=True)),
        )
        context['featured_categories'] = categories

        context['top_providers'] = (
            ProviderProfile.objects.filter(is_active=True, category__isnull=False)
            .select_related('user__userprofile', 'category')
            .annotate(avg_rating=Avg('reviews_received__rating'), rating_count=Count('reviews_received'))
            .filter(rating_count__gt=0)
            .order_by('-avg_rating', '-rating_count')[:4]
        )

        user = self.request.user
        if user.is_authenticated and getattr(user, 'userprofile', None) and user.userprofile.role == 'customer':
            from apps.bookings.models import Booking
            context['recent_bookings'] = Booking.objects.filter(
                customer=user.customer_profile,
            ).select_related('category', 'provider__user__userprofile').order_by('-created_at')[:3]

        return context


class SearchResultsView(TemplateView):
    """Provider Service Tag / Hashtag Search System — real server-side
    search (not a frontend-only filter). The customer's query is normalized
    with the exact same function used to store tags, then matched against
    ProviderTag.name, so 'fan', '#fan', 'Fan' and '#FAN' all return the same
    providers. If no provider has that exact tag, matching service
    categories are shown as a secondary signal — the existing category
    browse experience is untouched."""
    template_name = 'search_results.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.categories.models import ServiceCategory
        from apps.providers.models import ProviderProfile, normalize_tag

        raw_query = self.request.GET.get('q', '').strip()
        query = normalize_tag(raw_query)
        context['raw_query'] = raw_query
        context['query'] = query

        providers = ProviderProfile.objects.none()
        categories = ServiceCategory.objects.none()

        if query:
            providers = (
                ProviderProfile.objects.filter(is_active=True, service_tags__name=query)
                .select_related('user__userprofile', 'category')
                .prefetch_related('service_tags')
                .distinct()
            )
            if not providers.exists():
                categories = ServiceCategory.objects.filter(is_active=True, name__icontains=raw_query)

        context['providers'] = providers
        context['categories'] = categories
        return context


class AboutView(TemplateView):
    template_name = 'about.html'


class ContactView(TemplateView):
    template_name = 'contact.html'


def custom_404(request, exception=None):
    return render(request, 'errors/404.html', status=404)


def custom_403(request, exception=None):
    return render(request, 'errors/403.html', status=403)


def custom_500(request):
    return render(request, 'errors/500.html', status=500)
