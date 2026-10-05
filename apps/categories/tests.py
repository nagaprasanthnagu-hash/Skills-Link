from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.categories.models import ServiceCategory


class CategoryPublicViewTests(TestCase):
    def setUp(self):
        self.active = ServiceCategory.objects.create(name='Plumbing', is_active=True)
        self.inactive = ServiceCategory.objects.create(name='Retired Category', is_active=False)

    def test_list_shows_only_active_categories(self):
        response = self.client.get(reverse('categories:list'))
        self.assertContains(response, 'Plumbing')
        self.assertNotContains(response, 'Retired Category')

    def test_inactive_category_detail_not_found(self):
        response = self.client.get(reverse('categories:detail', args=[self.inactive.pk]))
        self.assertEqual(response.status_code, 404)


class CategoryAdminManagementTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username='admin2', email='admin2@example.com', password='AdminPass123')

    def test_non_admin_cannot_access_manage_list(self):
        user = User.objects.create_user(username='plaincustomer', email='pc@example.com', password='Pass1234')
        UserProfile.objects.create(user=user, full_name='Plain Customer', role=UserProfile.ROLE_CUSTOMER)
        self.client.login(username='plaincustomer', password='Pass1234')
        response = self.client.get(reverse('categories:manage_list'))
        self.assertNotEqual(response.status_code, 200)

    def test_admin_can_create_category(self):
        self.client.login(username='admin2', password='AdminPass123')
        response = self.client.post(reverse('categories:create'), {
            'name': 'Gardening', 'description': 'Lawn and garden maintenance', 'is_active': 'on',
        })
        self.assertRedirects(response, reverse('categories:manage_list'))
        self.assertTrue(ServiceCategory.objects.filter(name='Gardening').exists())

    def test_duplicate_category_name_rejected(self):
        ServiceCategory.objects.create(name='Plumbing')
        self.client.login(username='admin2', password='AdminPass123')
        response = self.client.post(reverse('categories:create'), {
            'name': 'Plumbing', 'description': '', 'is_active': 'on',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already exists')

    def test_admin_can_deactivate_category(self):
        category = ServiceCategory.objects.create(name='Cleaning', is_active=True)
        self.client.login(username='admin2', password='AdminPass123')
        self.client.post(reverse('categories:deactivate', args=[category.pk]))
        category.refresh_from_db()
        self.assertFalse(category.is_active)
