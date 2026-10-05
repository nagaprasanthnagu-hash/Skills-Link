from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.categories.models import ServiceCategory
from apps.providers.models import ProviderProfile


class ProviderProfileSetupTests(TestCase):
    def setUp(self):
        self.category = ServiceCategory.objects.create(name='Electrical', is_active=True)
        self.user = User.objects.create_user(username='provsetup', email='provsetup@example.com', password='Pass1234')
        UserProfile.objects.create(user=self.user, full_name='Prov Setup', role=UserProfile.ROLE_PROVIDER)
        ProviderProfile.objects.create(user=self.user)

    def test_provider_can_set_category_and_experience(self):
        self.client.login(username='provsetup', password='Pass1234')
        response = self.client.post(reverse('providers:profile_setup'), {
            'category': self.category.pk, 'experience_years': 5, 'bio': 'Skilled electrician.',
        })
        self.assertRedirects(response, reverse('providers:dashboard'))
        self.user.provider_profile.refresh_from_db()
        self.assertEqual(self.user.provider_profile.category, self.category)
        self.assertEqual(self.user.provider_profile.experience_years, 5)

    def test_invalid_experience_years_rejected(self):
        self.client.login(username='provsetup', password='Pass1234')
        response = self.client.post(reverse('providers:profile_setup'), {
            'category': self.category.pk, 'experience_years': 999, 'bio': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'valid number of years')

    def test_dashboard_flags_incomplete_profile(self):
        self.client.login(username='provsetup', password='Pass1234')
        response = self.client.get(reverse('providers:dashboard'))
        self.assertContains(response, 'incomplete')


class ProfilePhotoValidationTests(TestCase):
    """File-upload validation for ProviderProfile.profile_photo (and, by the
    same validator, WorkPhoto.image): correct image type, size ceiling."""

    def setUp(self):
        self.user = User.objects.create_user(username='photoprov', email='photoprov@example.com', password='Pass1234')
        UserProfile.objects.create(user=self.user, full_name='Photo Prov', role=UserProfile.ROLE_PROVIDER)
        self.provider = ProviderProfile.objects.create(user=self.user)

    def _tiny_png(self, name='ok.png'):
        from django.core.files.uploadedfile import SimpleUploadedFile
        png = bytes.fromhex(
            '89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de'
            '0000000c4944415408d763f8cfc0c00000030101007e4e7d5f0000000049454e44ae426082'
        )
        return SimpleUploadedFile(name, png, content_type='image/png')

    def test_valid_png_accepted(self):
        from django.core.exceptions import ValidationError
        from apps.providers.models import validate_profile_photo
        try:
            validate_profile_photo(self._tiny_png())
        except ValidationError:
            self.fail('a valid small PNG should not raise ValidationError')

    def test_non_image_file_type_rejected(self):
        from django.core.exceptions import ValidationError
        from django.core.files.uploadedfile import SimpleUploadedFile
        from apps.providers.models import validate_profile_photo
        fake = SimpleUploadedFile('not-a-photo.txt', b'just some text, not an image', content_type='text/plain')
        with self.assertRaises(ValidationError):
            validate_profile_photo(fake)

    def test_oversized_file_rejected(self):
        from django.core.exceptions import ValidationError
        from django.core.files.uploadedfile import SimpleUploadedFile
        from apps.providers.models import validate_profile_photo
        oversized = SimpleUploadedFile(
            'huge.jpg', b'\xff' * (3 * 1024 * 1024), content_type='image/jpeg',
        )
        with self.assertRaises(ValidationError):
            validate_profile_photo(oversized)

    def test_provider_profile_form_rejects_bad_upload(self):
        self.client.login(username='photoprov', password='Pass1234')
        from django.core.files.uploadedfile import SimpleUploadedFile
        category = ServiceCategory.objects.create(name='Cleaning', is_active=True)
        fake = SimpleUploadedFile('bad.txt', b'not an image', content_type='text/plain')
        response = self.client.post(reverse('providers:profile_setup'), {
            'category': category.pk, 'experience_years': 2, 'bio': '',
            'profile_photo': fake,
        })
        self.assertEqual(response.status_code, 200)
        self.provider.refresh_from_db()
        self.assertFalse(self.provider.profile_photo)


class NormalizeTagTests(TestCase):
    """normalize_tag() — the single normalization function used for both
    storage/uniqueness and search matching (Provider Service Tag / Hashtag
    Search System, Section 5)."""

    def test_plain_lowercase(self):
        from apps.providers.models import normalize_tag
        self.assertEqual(normalize_tag('fan'), 'fan')

    def test_leading_hash_stripped(self):
        from apps.providers.models import normalize_tag
        self.assertEqual(normalize_tag('#fan'), 'fan')

    def test_mixed_case(self):
        from apps.providers.models import normalize_tag
        self.assertEqual(normalize_tag('Fan'), 'fan')

    def test_hash_and_uppercase(self):
        from apps.providers.models import normalize_tag
        self.assertEqual(normalize_tag('#FAN'), 'fan')

    def test_leading_trailing_whitespace(self):
        from apps.providers.models import normalize_tag
        self.assertEqual(normalize_tag(' fan '), 'fan')

    def test_multi_word_tag(self):
        from apps.providers.models import normalize_tag
        self.assertEqual(normalize_tag('fanrepair'), 'fanrepair')
        self.assertEqual(normalize_tag('#fanrepair'), 'fanrepair')

    def test_unsafe_characters_stripped(self):
        from apps.providers.models import normalize_tag
        self.assertEqual(normalize_tag('<script>fan</script>'), 'scriptfanscript')
        self.assertEqual(normalize_tag('fan!! repair##'), 'fanrepair')

    def test_empty_and_hash_only_are_invalid(self):
        from apps.providers.models import normalize_tag
        self.assertEqual(normalize_tag(''), '')
        self.assertEqual(normalize_tag('   '), '')
        self.assertEqual(normalize_tag('#'), '')
        self.assertEqual(normalize_tag(None), '')


class ProviderTagOwnershipTests(TestCase):
    """Provider Service Tag / Hashtag Search System — Sections 6, 7, 14.
    Create/edit/delete, per-provider uniqueness, and the critical ownership
    check: a provider must never be able to touch another provider's tag."""

    def setUp(self):
        self.category = ServiceCategory.objects.create(name='Electrical', is_active=True)

        self.user_a = User.objects.create_user(username='provider_a', email='a@example.com', password='Pass1234')
        UserProfile.objects.create(user=self.user_a, full_name='Provider A', role=UserProfile.ROLE_PROVIDER)
        self.provider_a = ProviderProfile.objects.create(user=self.user_a, category=self.category)

        self.user_b = User.objects.create_user(username='provider_b', email='b@example.com', password='Pass1234')
        UserProfile.objects.create(user=self.user_b, full_name='Provider B', role=UserProfile.ROLE_PROVIDER)
        self.provider_b = ProviderProfile.objects.create(user=self.user_b, category=self.category)

    def test_provider_can_create_tag(self):
        from apps.providers.models import ProviderTag
        self.client.login(username='provider_a', password='Pass1234')
        response = self.client.post(reverse('providers:tags'), {'name': '#FanRepair'})
        self.assertRedirects(response, reverse('providers:tags'))
        self.assertTrue(ProviderTag.objects.filter(provider=self.provider_a, name='fanrepair').exists())

    def test_provider_can_edit_own_tag(self):
        from apps.providers.models import ProviderTag
        tag = ProviderTag.objects.create(provider=self.provider_a, name='fan')
        self.client.login(username='provider_a', password='Pass1234')
        response = self.client.post(reverse('providers:tag_edit', args=[tag.pk]), {'name': '#ceilingfan'})
        self.assertRedirects(response, reverse('providers:tags'))
        tag.refresh_from_db()
        self.assertEqual(tag.name, 'ceilingfan')

    def test_provider_can_delete_own_tag(self):
        from apps.providers.models import ProviderTag
        tag = ProviderTag.objects.create(provider=self.provider_a, name='fan')
        self.client.login(username='provider_a', password='Pass1234')
        self.client.post(reverse('providers:tag_delete', args=[tag.pk]))
        self.assertFalse(ProviderTag.objects.filter(pk=tag.pk).exists())

    def test_duplicate_tag_for_same_provider_rejected(self):
        from apps.providers.models import ProviderTag
        ProviderTag.objects.create(provider=self.provider_a, name='fan')
        self.client.login(username='provider_a', password='Pass1234')
        response = self.client.post(reverse('providers:tags'), {'name': 'FAN'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already have this tag')
        self.assertEqual(ProviderTag.objects.filter(provider=self.provider_a, name='fan').count(), 1)

    def test_different_providers_can_have_the_same_tag_name(self):
        from apps.providers.models import ProviderTag
        ProviderTag.objects.create(provider=self.provider_a, name='fan')
        self.client.login(username='provider_b', password='Pass1234')
        response = self.client.post(reverse('providers:tags'), {'name': '#fan'})
        self.assertRedirects(response, reverse('providers:tags'))
        self.assertTrue(ProviderTag.objects.filter(provider=self.provider_b, name='fan').exists())

    def test_empty_tag_rejected(self):
        self.client.login(username='provider_a', password='Pass1234')
        response = self.client.post(reverse('providers:tags'), {'name': '###'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter a valid tag')

    def test_provider_cannot_edit_another_providers_tag(self):
        """Security (Section 7): Provider B must not be able to edit
        Provider A's tag by guessing/changing the pk in the URL."""
        from apps.providers.models import ProviderTag
        tag = ProviderTag.objects.create(provider=self.provider_a, name='fan')
        self.client.login(username='provider_b', password='Pass1234')
        response = self.client.post(reverse('providers:tag_edit', args=[tag.pk]), {'name': 'hacked'})
        self.assertEqual(response.status_code, 404)
        tag.refresh_from_db()
        self.assertEqual(tag.name, 'fan')

    def test_provider_cannot_delete_another_providers_tag(self):
        """Security (Section 7): Provider B must not be able to delete
        Provider A's tag by manually posting to its delete URL."""
        from apps.providers.models import ProviderTag
        tag = ProviderTag.objects.create(provider=self.provider_a, name='fan')
        self.client.login(username='provider_b', password='Pass1234')
        response = self.client.post(reverse('providers:tag_delete', args=[tag.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(ProviderTag.objects.filter(pk=tag.pk).exists())

    def test_anonymous_cannot_access_tag_management(self):
        response = self.client.get(reverse('providers:tags'))
        self.assertNotEqual(response.status_code, 200)

    def test_customer_cannot_access_tag_management(self):
        customer_user = User.objects.create_user(username='cust1', email='c@example.com', password='Pass1234')
        UserProfile.objects.create(user=customer_user, full_name='Cust One', role=UserProfile.ROLE_CUSTOMER)
        from apps.customers.models import CustomerProfile
        CustomerProfile.objects.create(user=customer_user)
        self.client.login(username='cust1', password='Pass1234')
        response = self.client.get(reverse('providers:tags'))
        self.assertRedirects(response, reverse('customers:dashboard'))


class ProviderTagSearchTests(TestCase):
    """Customer-facing search (Sections 8, 9, 11) — real server-side lookup
    against ProviderTag, normalizing the query the same way tags are
    stored, so 'fan' / '#fan' / 'Fan' / '#FAN' / 'fanrepair' all resolve to
    the same providers."""

    def setUp(self):
        from apps.providers.models import ProviderTag

        self.category = ServiceCategory.objects.create(name='Electrical', is_active=True)

        self.user_a = User.objects.create_user(username='fanprovider', email='fan@example.com', password='Pass1234')
        UserProfile.objects.create(user=self.user_a, full_name='Fan Provider', role=UserProfile.ROLE_PROVIDER)
        self.provider_a = ProviderProfile.objects.create(user=self.user_a, category=self.category, is_active=True)
        ProviderTag.objects.create(provider=self.provider_a, name='fan')
        ProviderTag.objects.create(provider=self.provider_a, name='ceilingfan')
        ProviderTag.objects.create(provider=self.provider_a, name='fanrepair')

        self.user_b = User.objects.create_user(username='plumberprovider', email='plumber@example.com', password='Pass1234')
        UserProfile.objects.create(user=self.user_b, full_name='Plumber Provider', role=UserProfile.ROLE_PROVIDER)
        self.provider_b = ProviderProfile.objects.create(user=self.user_b, category=self.category, is_active=True)
        ProviderTag.objects.create(provider=self.provider_b, name='plumbing')

    def _search(self, q):
        return self.client.get(reverse('search'), {'q': q})

    def test_plain_query_matches(self):
        response = self._search('fan')
        self.assertContains(response, 'Fan Provider')

    def test_hash_prefixed_query_matches(self):
        response = self._search('#fan')
        self.assertContains(response, 'Fan Provider')

    def test_capitalized_query_matches(self):
        response = self._search('Fan')
        self.assertContains(response, 'Fan Provider')

    def test_hash_and_uppercase_query_matches(self):
        response = self._search('#FAN')
        self.assertContains(response, 'Fan Provider')

    def test_second_tag_matches_same_provider(self):
        response = self._search('fanrepair')
        self.assertContains(response, 'Fan Provider')
        response = self._search('#fanrepair')
        self.assertContains(response, 'Fan Provider')

    def test_unrelated_provider_not_returned(self):
        response = self._search('fan')
        self.assertNotContains(response, 'Plumber Provider')

    def test_different_provider_with_own_tag_is_found(self):
        response = self._search('plumbing')
        self.assertContains(response, 'Plumber Provider')
        self.assertNotContains(response, 'Fan Provider')

    def test_no_match_shows_empty_state_not_fake_results(self):
        response = self._search('carrepair')
        self.assertNotContains(response, 'Fan Provider')
        self.assertNotContains(response, 'Plumber Provider')

    def test_existing_category_search_still_works(self):
        """Section 9: category browsing (unrelated to tags) must keep working."""
        response = self.client.get(reverse('categories:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Electrical')
