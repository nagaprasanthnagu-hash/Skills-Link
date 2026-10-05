"""
DEMO / TESTING ONLY — Provider Service Tag / Hashtag Search System.

Attaches a small set of realistic service tags to EXISTING provider
accounts, purely so the tag search feature can be exercised end-to-end
(searching "fan", "#fan", "plumbing", "cleaning", etc.).

This is intentionally a manually-invoked management command — NOT run at
app startup, NOT a fixture, and NOT hard-coded into any production view,
signal, or migration — so it never runs unless a developer explicitly
types:

    python manage.py seed_demo_tags

It only ADDS ProviderTag rows to EXISTING ProviderProfile records already
in the database. It never creates providers/customers, and never creates
or touches bookings, reviews, ratings, or payments, and never changes a
provider's existing profile/category. It is safe to run more than once —
tags are looked up by (provider, normalized name) and skipped if already
present, so re-running just reports 0 new rows created.
"""
from django.core.management.base import BaseCommand

from apps.providers.models import ProviderProfile, ProviderTag, normalize_tag

# username -> tags to attach. Mapped to each existing provider's REAL
# category rather than the originally-suggested example roles (this dev
# database has Plumbing/Electrical/Cleaning/Painting/AC Repair providers,
# not a Carpenter or a dedicated Appliance-Repair/fridge provider) — see the
# implementation report for the full rationale.
DEMO_TAGS_BY_USERNAME = {
    'ravi_e': ['fan', 'fanrepair', 'ceilingfan', 'switchboard', 'wiring'],          # Electrical
    'suresh_p': ['plumbing', 'pipe', 'taprepair', 'waterleak'],                     # Plumbing
    'lakshmi_c': ['cleaning', 'homecleaning', 'deepcleaning', 'bathroomcleaning'],  # Cleaning
    'mani_p': ['painting', 'wallpainting', 'interiorpainting', 'paintrepair'],      # Painting
    'kumar_s': ['acrepair', 'airconditioner', 'acservice', 'accompressor'],         # AC Repair
}


class Command(BaseCommand):
    help = 'DEMO ONLY: attach sample service tags to existing provider accounts, for testing tag search.'

    def handle(self, *args, **options):
        created, skipped, missing_users = 0, 0, []

        for username, tags in DEMO_TAGS_BY_USERNAME.items():
            try:
                provider = ProviderProfile.objects.select_related('user').get(user__username=username)
            except ProviderProfile.DoesNotExist:
                missing_users.append(username)
                continue

            for raw_tag in tags:
                name = normalize_tag(raw_tag)
                if not name:
                    continue
                _, was_created = ProviderTag.objects.get_or_create(provider=provider, name=name)
                if was_created:
                    created += 1
                    self.stdout.write(f'  + #{name} -> {username} (provider id {provider.pk})')
                else:
                    skipped += 1

        self.stdout.write(self.style.SUCCESS(f'Done. {created} tag(s) created, {skipped} already existed.'))
        if missing_users:
            self.stdout.write(self.style.WARNING(
                f'Skipped — no provider with this username exists in this database: {", ".join(missing_users)}'
            ))
