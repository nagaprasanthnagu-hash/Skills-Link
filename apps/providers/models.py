import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

TAG_NAME_MAX_LENGTH = 40

# Only lowercase letters and digits survive normalization, so nothing that
# reaches the database can carry HTML/script/punctuation content.
_TAG_NAME_VALIDATOR = RegexValidator(
    regex=r'^[a-z0-9]+$',
    message='Tags may contain only lowercase letters and numbers.',
)


def normalize_tag(raw_value):
    """Canonicalize a provider service tag / hashtag for storage, uniqueness,
    and search matching (Provider Service Tag / Hashtag Search System).

    '#fan', 'Fan', ' fan ', '#FAN' and 'fan' all normalize to 'fan', so the
    same DB value is stored and searched regardless of how a provider or
    customer typed it. Only lowercase letters/digits are kept — everything
    else (including any HTML/script content) is stripped, never rendered.
    Returns '' when nothing usable remains; callers must treat that as
    invalid/empty rather than saving it.
    """
    if not raw_value:
        return ''
    value = raw_value.strip()
    if value.startswith('#'):
        value = value[1:]
    value = value.strip().lower()
    return re.sub(r'[^a-z0-9]', '', value)


def validate_profile_photo(file):
    """File upload validation (Section 62.4): JPEG/PNG only, max 2MB."""
    content_type = getattr(file, 'content_type', None)
    if content_type and content_type not in settings.ALLOWED_UPLOAD_IMAGE_TYPES:
        raise ValidationError('Please upload a JPEG or PNG image under 2 MB.')
    if file.size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise ValidationError('Please upload a JPEG or PNG image under 2 MB.')


class ProviderProfile(models.Model):
    """Extends User with provider-specific fields (Section 23, 58.3)."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='provider_profile',
    )
    category = models.ForeignKey(
        'categories.ServiceCategory', on_delete=models.PROTECT,
        related_name='providers', null=True, blank=True,
        help_text='Required before the provider can view or accept bookings (Section 23 validation rule).',
    )
    experience_years = models.PositiveIntegerField(default=0)
    bio = models.TextField(blank=True)
    profile_photo = models.ImageField(
        upload_to='provider_profile_photos/', blank=True, null=True,
        validators=[validate_profile_photo],
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Provider Profile'
        verbose_name_plural = 'Provider Profiles'
        indexes = [models.Index(fields=['category'])]

    def __str__(self):
        return f'Provider: {self.user.username}'

    @property
    def average_rating(self):
        from django.db.models import Avg
        result = self.reviews_received.aggregate(avg=Avg('rating'))
        return round(result['avg'], 1) if result['avg'] else None

    @property
    def review_count(self):
        return self.reviews_received.count()


class WorkPhoto(models.Model):
    """Completed-work photo a provider attaches to a finished booking, shown
    on their public profile's work gallery (SkillLink work-gallery upgrade)."""
    booking = models.ForeignKey(
        'bookings.Booking', on_delete=models.CASCADE, related_name='work_photos',
    )
    provider = models.ForeignKey(
        ProviderProfile, on_delete=models.CASCADE, related_name='work_photos',
    )
    image = models.ImageField(upload_to='work_photos/', validators=[validate_profile_photo])
    caption = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Work Photo'
        verbose_name_plural = 'Work Photos'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['provider']), models.Index(fields=['booking'])]

    def __str__(self):
        return f'Work photo for booking #{self.booking_id}'


class ProviderTag(models.Model):
    """A specific service/work keyword a provider can be found by (Provider
    Service Tag / Hashtag Search System). `name` is always the normalized
    form (see normalize_tag) — lowercase, alphanumeric, no leading '#' — so
    '#fan', 'Fan', '#FAN' and 'fan' are one and the same tag for both the
    per-provider uniqueness check and customer search matching."""
    provider = models.ForeignKey(
        ProviderProfile, on_delete=models.CASCADE, related_name='service_tags',
    )
    name = models.CharField(
        max_length=TAG_NAME_MAX_LENGTH,
        validators=[_TAG_NAME_VALIDATOR],
        help_text='Normalized tag (e.g. "fanrepair") — always displayed with a leading #.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Provider Service Tag'
        verbose_name_plural = 'Provider Service Tags'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['provider', 'name'], name='unique_provider_tag_name'),
        ]
        indexes = [
            models.Index(fields=['name'], name='providers_tag_name_idx'),
            models.Index(fields=['provider'], name='providers_tag_provider_idx'),
        ]

    def __str__(self):
        return f'#{self.name} ({self.provider.user.username})'

    @property
    def display(self):
        return f'#{self.name}'
