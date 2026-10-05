from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.customers.models import CustomerProfile


class CustomerDashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='custdash', email='custdash@example.com', password='Pass1234')
        UserProfile.objects.create(user=self.user, full_name='Cust Dash', role=UserProfile.ROLE_CUSTOMER)
        CustomerProfile.objects.create(user=self.user)

    def test_customer_can_access_dashboard(self):
        self.client.login(username='custdash', password='Pass1234')
        response = self.client.get(reverse('customers:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_provider_cannot_access_customer_dashboard(self):
        provider_user = User.objects.create_user(username='provx', email='provx@example.com', password='Pass1234')
        UserProfile.objects.create(user=provider_user, full_name='Prov X', role=UserProfile.ROLE_PROVIDER)
        from apps.providers.models import ProviderProfile
        ProviderProfile.objects.create(user=provider_user)
        self.client.login(username='provx', password='Pass1234')
        response = self.client.get(reverse('customers:dashboard'))
        self.assertRedirects(response, reverse('providers:dashboard'))

    def test_anonymous_redirected_to_login(self):
        response = self.client.get(reverse('customers:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)
