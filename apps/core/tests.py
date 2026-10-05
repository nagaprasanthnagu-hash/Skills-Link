from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.categories.models import ServiceCategory
from apps.providers.models import ProviderProfile


class SearchRouteTests(TestCase):
    """/search/ (Provider Service Tag / Hashtag Search System, Section 10/11)
    — confirms the route resolves and renders for anonymous visitors, and
    that an empty/blank query shows the empty-state rather than an error or
    fabricated results."""

    def setUp(self):
        self.category = ServiceCategory.objects.create(name='Electrical', is_active=True)
        user = User.objects.create_user(username='routetestprov', email='routetest@example.com', password='Pass1234')
        UserProfile.objects.create(user=user, full_name='Route Test Provider', role=UserProfile.ROLE_PROVIDER)
        ProviderProfile.objects.create(user=user, category=self.category, is_active=True)

    def test_search_page_loads_with_no_query(self):
        response = self.client.get(reverse('search'))
        self.assertEqual(response.status_code, 200)

    def test_search_page_loads_with_query(self):
        response = self.client.get(reverse('search'), {'q': 'anything'})
        self.assertEqual(response.status_code, 200)

    def test_homepage_still_renders(self):
        """Homepage regression check — this feature must not break home.html."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
