from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.categories.models import ServiceCategory
from apps.customers.models import CustomerProfile
from apps.providers.models import ProviderProfile


class AdminDashboardAccessTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username='dashadmin', email='dashadmin@example.com', password='AdminPass123')

        self.customer_user = User.objects.create_user(username='dashcust', email='dashcust@example.com', password='Pass1234')
        UserProfile.objects.create(user=self.customer_user, full_name='Dash Cust', role=UserProfile.ROLE_CUSTOMER)
        CustomerProfile.objects.create(user=self.customer_user)

    def test_non_admin_redirected_from_dashboard(self):
        self.client.login(username='dashcust', password='Pass1234')
        response = self.client.get(reverse('dashboard:index'))
        self.assertRedirects(response, reverse('customers:dashboard'))

    def test_anonymous_redirected_to_login(self):
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)

    def test_admin_dashboard_shows_counts(self):
        ServiceCategory.objects.create(name='Test Category', is_active=True)
        self.client.login(username='dashadmin', password='AdminPass123')
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Admin Dashboard')

    def test_admin_can_deactivate_user(self):
        self.client.login(username='dashadmin', password='AdminPass123')
        response = self.client.post(reverse('dashboard:users'), {'user_id': self.customer_user.pk})
        self.assertRedirects(response, reverse('dashboard:users'))
        self.customer_user.refresh_from_db()
        self.assertFalse(self.customer_user.is_active)

    def test_admin_can_deactivate_provider(self):
        provider_user = User.objects.create_user(username='dashprov', email='dashprov@example.com', password='Pass1234')
        UserProfile.objects.create(user=provider_user, full_name='Dash Prov', role=UserProfile.ROLE_PROVIDER)
        provider = ProviderProfile.objects.create(user=provider_user, is_active=True)

        self.client.login(username='dashadmin', password='AdminPass123')
        response = self.client.post(reverse('dashboard:providers'), {'provider_id': provider.pk})
        self.assertRedirects(response, reverse('dashboard:providers'))
        provider.refresh_from_db()
        self.assertFalse(provider.is_active)
