from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

PHONE_VALIDATOR = RegexValidator(
    regex=r'^\+?[0-9]{7,15}$',
    message='Please enter a valid phone number.',
)


class CustomerProfile(models.Model):
    """Extends User with customer-specific fields (Section 22, 58.2)."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer_profile',
    )
    phone = models.CharField(max_length=15, blank=True, validators=[PHONE_VALIDATOR])
    default_address = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Customer Profile'
        verbose_name_plural = 'Customer Profiles'

    def __str__(self):
        return f'Customer: {self.user.username}'
