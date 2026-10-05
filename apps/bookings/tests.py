from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import UserProfile
from apps.bookings import services
from apps.bookings.models import Booking, BookingStatusLog
from apps.categories.models import ServiceCategory
from apps.customers.models import CustomerProfile
from apps.providers.models import ProviderProfile


class BookingServiceTests(TestCase):
    """Unit tests directly against the state-machine service layer."""

    def setUp(self):
        self.category = ServiceCategory.objects.create(name='Plumbing', is_active=True)
        self.other_category = ServiceCategory.objects.create(name='Electrical', is_active=True)

        customer_user = User.objects.create_user(username='cust1', email='cust1@example.com', password='Pass1234')
        UserProfile.objects.create(user=customer_user, full_name='Cust One', role=UserProfile.ROLE_CUSTOMER)
        self.customer = CustomerProfile.objects.create(user=customer_user)

        provider_user = User.objects.create_user(username='prov1', email='prov1@example.com', password='Pass1234')
        UserProfile.objects.create(user=provider_user, full_name='Prov One', role=UserProfile.ROLE_PROVIDER)
        self.provider = ProviderProfile.objects.create(user=provider_user, category=self.category)

        other_provider_user = User.objects.create_user(username='prov2', email='prov2@example.com', password='Pass1234')
        UserProfile.objects.create(user=other_provider_user, full_name='Prov Two', role=UserProfile.ROLE_PROVIDER)
        self.other_provider = ProviderProfile.objects.create(user=other_provider_user, category=self.other_category)

    def _make_booking(self):
        return services.create_booking(
            customer_profile=self.customer,
            category=self.category,
            preferred_datetime=timezone.now() + timedelta(days=1),
            address='123 Test Street',
            description='A sample plumbing issue that needs fixing.',
        )

    def test_create_booking_logs_pending_status(self):
        booking = self._make_booking()
        self.assertEqual(booking.status, Booking.STATUS_PENDING)
        self.assertEqual(BookingStatusLog.objects.filter(booking=booking).count(), 1)

    def test_accept_booking_assigns_provider_and_transitions(self):
        booking = self._make_booking()
        services.accept_booking(booking, self.provider)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.STATUS_ACCEPTED)
        self.assertEqual(booking.provider, self.provider)

    def test_accept_booking_rejects_mismatched_category(self):
        booking = self._make_booking()
        with self.assertRaises(PermissionDenied):
            services.accept_booking(booking, self.other_provider)

    def test_inactive_provider_cannot_accept_booking(self):
        self.provider.is_active = False
        self.provider.save(update_fields=['is_active'])
        booking = self._make_booking()
        with self.assertRaises(PermissionDenied):
            services.accept_booking(booking, self.provider)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.STATUS_PENDING)

    def test_inactive_category_cannot_be_accepted_into(self):
        booking = self._make_booking()
        self.category.is_active = False
        self.category.save(update_fields=['is_active'])
        with self.assertRaises(PermissionDenied):
            services.accept_booking(booking, self.provider)

    def test_concurrent_acceptance_only_one_provider_wins(self):
        """Two providers in the same category race to accept the same
        booking; select_for_update() must let exactly one of them win.
        See ConcurrentBookingAcceptanceTests below for the real threaded
        version — TestCase wraps this test in an outer transaction that a
        second thread's own connection can't see, so it can only assert
        the mechanism exists, not exercise true concurrent access."""
        booking = self._make_booking()
        services.accept_booking(booking, self.provider)
        with self.assertRaises(services.InvalidTransitionError):
            services.accept_booking(booking, self.other_provider)

    def test_cannot_accept_already_accepted_booking(self):
        booking = self._make_booking()
        services.accept_booking(booking, self.provider)
        with self.assertRaises(services.InvalidTransitionError):
            services.accept_booking(booking, self.provider)

    def test_advance_status_forward_only(self):
        booking = self._make_booking()
        booking = services.accept_booking(booking, self.provider)
        services.advance_status(booking, self.provider, Booking.STATUS_IN_PROGRESS)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.STATUS_IN_PROGRESS)

        services.advance_status(booking, self.provider, Booking.STATUS_COMPLETED)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.STATUS_COMPLETED)

    def test_cannot_skip_status(self):
        booking = self._make_booking()
        booking = services.accept_booking(booking, self.provider)
        with self.assertRaises(services.InvalidTransitionError):
            services.advance_status(booking, self.provider, Booking.STATUS_COMPLETED)

    def test_unassigned_provider_cannot_advance_status(self):
        booking = self._make_booking()
        booking = services.accept_booking(booking, self.provider)
        with self.assertRaises(PermissionDenied):
            services.advance_status(booking, self.other_provider, Booking.STATUS_IN_PROGRESS)

    def test_customer_can_cancel_pending_booking(self):
        booking = self._make_booking()
        services.cancel_booking(booking, self.customer)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.STATUS_CANCELLED)

    def test_cannot_cancel_completed_booking(self):
        booking = self._make_booking()
        booking = services.accept_booking(booking, self.provider)
        booking = services.advance_status(booking, self.provider, Booking.STATUS_IN_PROGRESS)
        services.advance_status(booking, self.provider, Booking.STATUS_COMPLETED)
        with self.assertRaises(services.InvalidTransitionError):
            services.cancel_booking(booking, self.customer)

    def test_other_customer_cannot_cancel_booking(self):
        booking = self._make_booking()
        other_customer_user = User.objects.create_user(username='cust2', email='cust2@example.com', password='Pass1234')
        UserProfile.objects.create(user=other_customer_user, full_name='Cust Two', role=UserProfile.ROLE_CUSTOMER)
        other_customer = CustomerProfile.objects.create(user=other_customer_user)
        with self.assertRaises(PermissionDenied):
            services.cancel_booking(booking, other_customer)


class BookingViewTests(TestCase):
    """Integration tests through the HTTP layer."""

    def setUp(self):
        self.category = ServiceCategory.objects.create(name='Cleaning', is_active=True)

        customer_user = User.objects.create_user(username='viewcust', email='viewcust@example.com', password='Pass1234')
        UserProfile.objects.create(user=customer_user, full_name='View Cust', role=UserProfile.ROLE_CUSTOMER)
        self.customer = CustomerProfile.objects.create(user=customer_user)

        provider_user = User.objects.create_user(username='viewprov', email='viewprov@example.com', password='Pass1234')
        UserProfile.objects.create(user=provider_user, full_name='View Prov', role=UserProfile.ROLE_PROVIDER)
        self.provider = ProviderProfile.objects.create(user=provider_user, category=self.category)

    def test_customer_can_create_booking_via_form(self):
        self.client.login(username='viewcust', password='Pass1234')
        future = (timezone.now() + timedelta(days=2)).strftime('%Y-%m-%dT%H:%M')
        response = self.client.post(reverse('bookings:create'), {
            'category': self.category.pk,
            'preferred_datetime': future,
            'address': '55 Test Road',
            'description': 'Deep cleaning required for a two-bedroom apartment.',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Booking.objects.filter(customer=self.customer).exists())

    def test_past_datetime_rejected(self):
        self.client.login(username='viewcust', password='Pass1234')
        past = (timezone.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        response = self.client.post(reverse('bookings:create'), {
            'category': self.category.pk,
            'preferred_datetime': past,
            'address': '55 Test Road',
            'description': 'Deep cleaning required for a two-bedroom apartment.',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'future date and time')

    def test_provider_cannot_create_booking(self):
        self.client.login(username='viewprov', password='Pass1234')
        response = self.client.get(reverse('bookings:create'))
        self.assertRedirects(response, reverse('providers:dashboard'))

    def test_provider_accept_via_view(self):
        booking = services.create_booking(
            customer_profile=self.customer, category=self.category,
            preferred_datetime=timezone.now() + timedelta(days=1),
            address='1 Test Ave', description='Sample cleaning description text.',
        )
        self.client.login(username='viewprov', password='Pass1234')
        response = self.client.post(reverse('bookings:accept', args=[booking.pk]))
        self.assertRedirects(response, reverse('bookings:detail', args=[booking.pk]))
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.STATUS_ACCEPTED)

    def test_unrelated_customer_cannot_view_booking_detail(self):
        booking = services.create_booking(
            customer_profile=self.customer, category=self.category,
            preferred_datetime=timezone.now() + timedelta(days=1),
            address='1 Test Ave', description='Sample cleaning description text.',
        )
        other_user = User.objects.create_user(username='intruder', email='intruder@example.com', password='Pass1234')
        UserProfile.objects.create(user=other_user, full_name='Intruder', role=UserProfile.ROLE_CUSTOMER)
        CustomerProfile.objects.create(user=other_user)
        self.client.login(username='intruder', password='Pass1234')
        response = self.client.get(reverse('bookings:detail', args=[booking.pk]))
        self.assertRedirects(response, reverse('customers:dashboard'))


class ConcurrentBookingAcceptanceTests(TransactionTestCase):
    """Real multi-threaded race test against the select_for_update() lock
    in accept_booking(). Needs TransactionTestCase (not TestCase) so each
    thread's own DB connection can actually see committed rows — TestCase's
    outer-transaction wrapping would hide them from a second connection."""

    def setUp(self):
        self.category = ServiceCategory.objects.create(name='Plumbing', is_active=True)
        customer_user = User.objects.create_user(username='racecust', email='racecust@example.com', password='Pass1234')
        UserProfile.objects.create(user=customer_user, full_name='Race Cust', role=UserProfile.ROLE_CUSTOMER)
        self.customer = CustomerProfile.objects.create(user=customer_user)

        self.provider_a = self._make_provider('racepa')
        self.provider_b = self._make_provider('racepb')

        self.booking = services.create_booking(
            customer_profile=self.customer, category=self.category,
            preferred_datetime=timezone.now() + timedelta(days=1),
            address='1 Race St', description='Race condition test booking.',
        )

    def _make_provider(self, username):
        user = User.objects.create_user(username=username, email=f'{username}@example.com', password='Pass1234')
        UserProfile.objects.create(user=user, full_name=username, role=UserProfile.ROLE_PROVIDER)
        return ProviderProfile.objects.create(user=user, category=self.category)

    def test_only_one_provider_wins_the_race(self):
        import threading
        from django.db import connection
        from django.db.utils import OperationalError

        results = []
        barrier = threading.Barrier(2)

        def _attempt(provider):
            try:
                barrier.wait(timeout=5)
                services.accept_booking(self.booking, provider)
                results.append('won')
            except (services.InvalidTransitionError, PermissionDenied):
                results.append('lost')
            except OperationalError:
                # SQLite (dev/test db) has no real row-level SELECT FOR
                # UPDATE — concurrent writers can surface as a raw
                # "database is locked" error instead of our clean
                # application exception. On PostgreSQL (production) the
                # same select_for_update() blocks the second transaction
                # until the first commits, and it then cleanly hits
                # InvalidTransitionError instead. Either way, losing the
                # race is losing the race.
                results.append('lost')
            finally:
                connection.close()

        t1 = threading.Thread(target=_attempt, args=(self.provider_a,))
        t2 = threading.Thread(target=_attempt, args=(self.provider_b,))
        t1.start(); t2.start()
        t1.join(timeout=10); t2.join(timeout=10)

        self.assertEqual(results.count('won'), 1, f'expected exactly one winner, got: {results}')
        self.assertEqual(results.count('lost'), 1, f'expected exactly one loser, got: {results}')

        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.STATUS_ACCEPTED)
        self.assertIn(self.booking.provider_id, [self.provider_a.id, self.provider_b.id])
