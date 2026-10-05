from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import UserProfile
from apps.bookings.models import Booking
from apps.categories.models import ServiceCategory
from apps.customers.models import CustomerProfile
from apps.providers.models import ProviderProfile
from apps.reviews.models import Review


class ReviewTests(TestCase):
    def setUp(self):
        self.category = ServiceCategory.objects.create(name='Painting', is_active=True)

        customer_user = User.objects.create_user(username='revcust', email='revcust@example.com', password='Pass1234')
        UserProfile.objects.create(user=customer_user, full_name='Rev Cust', role=UserProfile.ROLE_CUSTOMER)
        self.customer = CustomerProfile.objects.create(user=customer_user)

        provider_user = User.objects.create_user(username='revprov', email='revprov@example.com', password='Pass1234')
        UserProfile.objects.create(user=provider_user, full_name='Rev Prov', role=UserProfile.ROLE_PROVIDER)
        self.provider = ProviderProfile.objects.create(user=provider_user, category=self.category)

        self.completed_booking = Booking.objects.create(
            customer=self.customer, provider=self.provider, category=self.category,
            preferred_datetime=timezone.now() + timedelta(days=1),
            address='Test address', description='Sample painting job description.',
            status=Booking.STATUS_COMPLETED,
        )
        self.pending_booking = Booking.objects.create(
            customer=self.customer, category=self.category,
            preferred_datetime=timezone.now() + timedelta(days=1),
            address='Test address', description='Sample painting job description.',
            status=Booking.STATUS_PENDING,
        )

    def test_customer_can_review_completed_booking(self):
        self.client.login(username='revcust', password='Pass1234')
        response = self.client.post(reverse('reviews:create', args=[self.completed_booking.pk]), {
            'rating': '5', 'comment': 'Great work, very tidy.',
        })
        self.assertRedirects(response, reverse('bookings:detail', args=[self.completed_booking.pk]))
        self.assertTrue(Review.objects.filter(booking=self.completed_booking).exists())

    def test_cannot_review_pending_booking(self):
        self.client.login(username='revcust', password='Pass1234')
        response = self.client.get(reverse('reviews:create', args=[self.pending_booking.pk]))
        self.assertEqual(response.status_code, 404)

    def test_cannot_review_same_booking_twice(self):
        Review.objects.create(booking=self.completed_booking, customer=self.customer, provider=self.provider, rating=4)
        self.client.login(username='revcust', password='Pass1234')
        response = self.client.get(reverse('reviews:create', args=[self.completed_booking.pk]))
        self.assertRedirects(response, reverse('bookings:detail', args=[self.completed_booking.pk]))

    def test_invalid_rating_rejected(self):
        self.client.login(username='revcust', password='Pass1234')
        response = self.client.post(reverse('reviews:create', args=[self.completed_booking.pk]), {
            'rating': '9', 'comment': 'Invalid rating test.',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Review.objects.filter(booking=self.completed_booking).exists())

    def test_provider_average_rating_calculation(self):
        Review.objects.create(booking=self.completed_booking, customer=self.customer, provider=self.provider, rating=4)
        self.assertEqual(self.provider.average_rating, 4.0)

    def test_provider_reviews_list_public(self):
        Review.objects.create(booking=self.completed_booking, customer=self.customer, provider=self.provider, rating=5, comment='Superb.')
        response = self.client.get(reverse('reviews:provider_reviews', args=[self.provider.pk]))
        self.assertContains(response, 'Superb.')
