"""
Seed demo data management command (Deliverables: "Seed Demo Data").

Usage: python manage.py seed_demo_data [--flush]

Creates a realistic demo dataset: categories, customers, providers,
bookings across every status, and reviews — enough to exercise every
screen without manual data entry.
"""
import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import UserProfile
from apps.bookings.models import Booking, BookingStatusLog
from apps.categories.models import ServiceCategory
from apps.customers.models import CustomerProfile
from apps.providers.models import ProviderProfile
from apps.reviews.models import Review

CATEGORIES = [
    ('Plumbing', 'Leak repair, pipe fitting, fixture installation'),
    ('Electrical', 'Wiring, switchboard repair, appliance installation'),
    ('Cleaning', 'Home deep cleaning, sofa and carpet cleaning'),
    ('Painting', 'Interior and exterior painting, waterproofing'),
    ('AC Repair', 'AC servicing, gas refill, installation'),
    ('Appliance Repair', 'Washing machine, refrigerator, and microwave repair'),
    ('Carpentry', 'Furniture repair, custom woodwork, door/window fitting'),
]

CUSTOMERS = [
    ('meena_h', 'Meena Harikrishnan', 'meena@example.com'),
    ('arjun_r', 'Arjun Ramasamy', 'arjun@example.com'),
    ('divya_k', 'Divya Krishnan', 'divya@example.com'),
]

PROVIDERS = [
    ('suresh_p', 'Suresh Pillai', 'suresh@example.com', 'Plumbing', 8, 'Licensed plumber with 8 years of residential experience.'),
    ('ravi_e', 'Ravi Elango', 'ravi@example.com', 'Electrical', 6, 'Certified electrician specialising in home wiring and repairs.'),
    ('lakshmi_c', 'Lakshmi Chandran', 'lakshmi@example.com', 'Cleaning', 4, 'Deep-cleaning specialist for homes and offices.'),
    ('mani_p', 'Mani Palanisamy', 'mani@example.com', 'Painting', 10, 'Interior and exterior painting expert.'),
    ('kumar_s', 'Kumar Selvam', 'kumar@example.com', 'AC Repair', 5, 'AC servicing and installation technician.'),
]


class Command(BaseCommand):
    help = 'Seeds the database with demo categories, customers, providers, bookings, and reviews.'

    def add_arguments(self, parser):
        parser.add_argument('--flush', action='store_true', help='Delete existing demo data before seeding.')

    def handle(self, *args, **options):
        if options['flush']:
            self.stdout.write('Flushing existing non-superuser data...')
            Review.objects.all().delete()
            BookingStatusLog.objects.all().delete()
            Booking.objects.all().delete()
            ProviderProfile.objects.all().delete()
            CustomerProfile.objects.all().delete()
            UserProfile.objects.filter(role__in=['customer', 'provider']).delete()
            User.objects.filter(is_superuser=False).delete()
            ServiceCategory.objects.all().delete()

        categories = self._seed_categories()
        customers = self._seed_customers()
        providers = self._seed_providers(categories)
        self._seed_bookings(customers, providers, categories)

        self.stdout.write(self.style.SUCCESS('Demo data seeded successfully.'))
        self.stdout.write('Demo accounts (password for all: DemoPass123):')
        for username, *_ in CUSTOMERS:
            self.stdout.write(f'  Customer -> username: {username}')
        for username, *_ in PROVIDERS:
            self.stdout.write(f'  Provider -> username: {username}')

    def _seed_categories(self):
        categories = {}
        for name, description in CATEGORIES:
            category, _ = ServiceCategory.objects.get_or_create(
                name=name, defaults={'description': description, 'is_active': True},
            )
            categories[name] = category
        self.stdout.write(f'Seeded {len(categories)} categories.')
        return categories

    def _seed_customers(self):
        customers = []
        for username, full_name, email in CUSTOMERS:
            user, created = User.objects.get_or_create(
                username=username, defaults={'email': email, 'first_name': full_name.split(' ')[0]},
            )
            if created:
                user.set_password('DemoPass123')
                user.save()
                UserProfile.objects.create(user=user, full_name=full_name, role=UserProfile.ROLE_CUSTOMER)
                CustomerProfile.objects.create(
                    user=user, phone='987654321' + str(random.randint(0, 9)),
                    default_address=f'{random.randint(1, 99)} Lake View Street, Uthamapalayam',
                )
            customers.append(user.customer_profile)
        self.stdout.write(f'Seeded {len(customers)} customers.')
        return customers

    def _seed_providers(self, categories):
        providers = []
        for username, full_name, email, category_name, years, bio in PROVIDERS:
            user, created = User.objects.get_or_create(
                username=username, defaults={'email': email, 'first_name': full_name.split(' ')[0]},
            )
            if created:
                user.set_password('DemoPass123')
                user.save()
                UserProfile.objects.create(user=user, full_name=full_name, role=UserProfile.ROLE_PROVIDER)
                ProviderProfile.objects.create(
                    user=user, category=categories[category_name],
                    experience_years=years, bio=bio, is_active=True,
                )
            providers.append(user.provider_profile)
        self.stdout.write(f'Seeded {len(providers)} providers.')
        return providers

    def _seed_bookings(self, customers, providers, categories):
        if Booking.objects.exists():
            self.stdout.write('Bookings already exist — skipping booking seed.')
            return

        now = timezone.now()
        scenarios = [
            (Booking.STATUS_PENDING, None),
            (Booking.STATUS_ACCEPTED, providers[0]),
            (Booking.STATUS_IN_PROGRESS, providers[1]),
            (Booking.STATUS_COMPLETED, providers[2]),
            (Booking.STATUS_COMPLETED, providers[3]),
            (Booking.STATUS_CANCELLED, None),
        ]

        count = 0
        for status, provider in scenarios:
            customer = random.choice(customers)
            category = provider.category if provider else random.choice(list(categories.values()))
            booking = Booking.objects.create(
                customer=customer,
                provider=provider,
                category=category,
                preferred_datetime=now + timedelta(days=random.randint(1, 7), hours=random.randint(1, 8)),
                address=customer.default_address or 'Demo address, Uthamapalayam',
                description=f'Sample {category.name.lower()} service request generated by seed data.',
                status=status,
            )
            BookingStatusLog.objects.create(booking=booking, old_status=None, new_status=Booking.STATUS_PENDING)
            if status != Booking.STATUS_PENDING:
                BookingStatusLog.objects.create(booking=booking, old_status=Booking.STATUS_PENDING, new_status=status)
            count += 1

            if status == Booking.STATUS_COMPLETED:
                Review.objects.create(
                    booking=booking, customer=customer, provider=provider,
                    rating=random.randint(4, 5),
                    comment='Quick, tidy work — would book again.',
                )

        self.stdout.write(f'Seeded {count} bookings with realistic status coverage.')
