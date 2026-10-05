from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import PasswordResetOTP, UserProfile


class RegistrationTests(TestCase):
    def test_customer_registration_creates_user_and_profile(self):
        response = self.client.post(reverse('accounts:register'), {
            'role': 'customer',
            'full_name': 'Test Customer',
            'username': 'testcustomer',
            'email': 'testcustomer@example.com',
            'password': 'TestPass123',
            'confirm_password': 'TestPass123',
        })
        self.assertRedirects(response, reverse('accounts:login'))
        user = User.objects.get(username='testcustomer')
        self.assertEqual(user.userprofile.role, UserProfile.ROLE_CUSTOMER)
        self.assertTrue(hasattr(user, 'customer_profile'))

    def test_provider_registration_creates_provider_profile(self):
        self.client.post(reverse('accounts:register'), {
            'role': 'provider',
            'full_name': 'Test Provider',
            'username': 'testprovider',
            'email': 'testprovider@example.com',
            'password': 'TestPass123',
            'confirm_password': 'TestPass123',
        })
        user = User.objects.get(username='testprovider')
        self.assertEqual(user.userprofile.role, UserProfile.ROLE_PROVIDER)
        self.assertTrue(hasattr(user, 'provider_profile'))

    def test_duplicate_username_rejected(self):
        User.objects.create_user(username='dupeuser', email='a@example.com', password='x')
        response = self.client.post(reverse('accounts:register'), {
            'role': 'customer',
            'full_name': 'Dupe User',
            'username': 'dupeuser',
            'email': 'unique@example.com',
            'password': 'TestPass123',
            'confirm_password': 'TestPass123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already taken')

    def test_password_mismatch_rejected(self):
        response = self.client.post(reverse('accounts:register'), {
            'role': 'customer',
            'full_name': 'Test User',
            'username': 'mismatchuser',
            'email': 'mismatch@example.com',
            'password': 'TestPass123',
            'confirm_password': 'Different123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'do not match')


class LoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='loginuser', email='login@example.com', password='TestPass123')
        UserProfile.objects.create(user=self.user, full_name='Login User', role=UserProfile.ROLE_CUSTOMER)
        from apps.customers.models import CustomerProfile
        CustomerProfile.objects.create(user=self.user)

    def test_login_with_username(self):
        response = self.client.post(reverse('accounts:login'), {
            'username_or_email': 'loginuser', 'password': 'TestPass123',
        })
        self.assertRedirects(response, reverse('accounts:post_login_redirect'), target_status_code=302)

    def test_login_with_email(self):
        response = self.client.post(reverse('accounts:login'), {
            'username_or_email': 'login@example.com', 'password': 'TestPass123',
        })
        self.assertRedirects(response, reverse('accounts:post_login_redirect'), target_status_code=302)

    def test_invalid_credentials_rejected(self):
        response = self.client.post(reverse('accounts:login'), {
            'username_or_email': 'loginuser', 'password': 'WrongPass',
        })
        self.assertContains(response, 'Invalid username/email or password')

    def test_role_based_redirect_for_customer(self):
        self.client.login(username='loginuser', password='TestPass123')
        response = self.client.get(reverse('accounts:post_login_redirect'))
        self.assertRedirects(response, reverse('customers:dashboard'))

    def test_login_locked_out_after_too_many_failed_attempts(self):
        from django.conf import settings as django_settings
        from django.core.cache import cache
        cache.clear()

        for _ in range(django_settings.LOGIN_RATE_LIMIT_ATTEMPTS):
            self.client.post(reverse('accounts:login'), {
                'username_or_email': 'loginuser', 'password': 'WrongPass',
            })

        # Even correct credentials must now be blocked for this IP.
        response = self.client.post(reverse('accounts:login'), {
            'username_or_email': 'loginuser', 'password': 'TestPass123',
        }, follow=True)
        self.assertContains(response, 'Too many failed login attempts')
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        cache.clear()


class PasswordResetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='resetuser', email='reset@example.com', password='OldPass123')
        UserProfile.objects.create(user=self.user, full_name='Reset User', role=UserProfile.ROLE_CUSTOMER)

    def test_otp_issued_and_password_reset(self):
        self.client.post(reverse('accounts:password_reset'), {'email': 'reset@example.com'})
        otp = PasswordResetOTP.objects.filter(user=self.user).latest('created_at')
        response = self.client.post(reverse('accounts:password_reset_verify'), {
            'otp_code': otp.otp_code, 'new_password': 'NewPass123', 'confirm_password': 'NewPass123',
        })
        self.assertRedirects(response, reverse('accounts:login'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass123'))

    def test_invalid_otp_rejected(self):
        self.client.post(reverse('accounts:password_reset'), {'email': 'reset@example.com'})
        response = self.client.post(reverse('accounts:password_reset_verify'), {
            'otp_code': '000000', 'new_password': 'NewPass123', 'confirm_password': 'NewPass123',
        })
        self.assertRedirects(response, reverse('accounts:password_reset'))

    def test_expired_otp_rejected(self):
        from datetime import timedelta
        from django.utils import timezone

        self.client.post(reverse('accounts:password_reset'), {'email': 'reset@example.com'})
        otp = PasswordResetOTP.objects.filter(user=self.user).latest('created_at')
        otp.expires_at = timezone.now() - timedelta(minutes=1)
        otp.save(update_fields=['expires_at'])

        response = self.client.post(reverse('accounts:password_reset_verify'), {
            'otp_code': otp.otp_code, 'new_password': 'NewPass123', 'confirm_password': 'NewPass123',
        })
        self.assertRedirects(response, reverse('accounts:password_reset'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('OldPass123'))

    def test_otp_cannot_be_reused(self):
        self.client.post(reverse('accounts:password_reset'), {'email': 'reset@example.com'})
        otp = PasswordResetOTP.objects.filter(user=self.user).latest('created_at')

        first = self.client.post(reverse('accounts:password_reset_verify'), {
            'otp_code': otp.otp_code, 'new_password': 'NewPass123', 'confirm_password': 'NewPass123',
        })
        self.assertRedirects(first, reverse('accounts:login'))

        second = self.client.post(reverse('accounts:password_reset_verify'), {
            'otp_code': otp.otp_code, 'new_password': 'AnotherPass123', 'confirm_password': 'AnotherPass123',
        })
        self.assertRedirects(second, reverse('accounts:password_reset'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass123'))

    def test_password_reset_does_not_reveal_whether_email_exists(self):
        known = self.client.post(reverse('accounts:password_reset'), {'email': 'reset@example.com'})
        unknown = self.client.post(reverse('accounts:password_reset'), {'email': 'nobody@example.com'})
        self.assertEqual(known.status_code, unknown.status_code)
        self.assertEqual(known.get('Location'), unknown.get('Location'))
