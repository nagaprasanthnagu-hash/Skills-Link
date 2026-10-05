"""
Root URL configuration (Section 56.5 / Section 59 of the PRD).

Every app's urls.py is included under a namespaced prefix so that
{% url %} tags remain unambiguous across the whole project
(e.g. {% url 'bookings:detail' pk=booking.id %}).
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Public routes (Section 59.1)
    path('', core_views.HomeView.as_view(), name='home'),
    path('search/', core_views.SearchResultsView.as_view(), name='search'),
    path('about/', core_views.AboutView.as_view(), name='about'),
    path('contact/', core_views.ContactView.as_view(), name='contact'),

    # App namespaces (Section 59.2 - 59.8)
    path('accounts/', include('apps.accounts.urls')),
    path('categories/', include('apps.categories.urls')),
    path('customers/', include('apps.customers.urls')),
    path('providers/', include('apps.providers.urls')),
    path('bookings/', include('apps.bookings.urls')),
    path('reviews/', include('apps.reviews.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'apps.core.views.custom_404'
handler403 = 'apps.core.views.custom_403'
handler500 = 'apps.core.views.custom_500'
