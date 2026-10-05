import random
import string
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    """
    Extends Django's built-in User with the role field (Section 20 design
    note): the role is stored on a one-to-one profile record rather than by
    subclassing the User model directly, which keeps future role additions
    a low-risk schema change.
    """
    ROLE_CUSTOMER = 'customer'
    ROLE_PROVIDER = 'provider'
    ROLE_ADMIN = 'admin'
    ROLE_CHOICES = [
        (ROLE_CUSTOMER, 'Customer'),
        (ROLE_PROVIDER, 'Service Provider'),
        (ROLE_ADMIN, 'Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    full_name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f'{self.full_name} ({self.get_role_display()})'


class PasswordResetOTP(models.Model):
    """One-time password for the forgot-password flow (FR-A4, Section 20)."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_otps')
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Password Reset OTP'
        verbose_name_plural = 'Password Reset OTPs'
        indexes = [models.Index(fields=['user', 'is_used'])]

    def __str__(self):
        return f'OTP for {self.user.username} ({"used" if self.is_used else "active"})'

    @staticmethod
    def generate_code():
        return ''.join(random.choices(string.digits, k=6))

    @classmethod
    def issue_for(cls, user):
        validity = getattr(settings, 'OTP_VALIDITY_MINUTES', 10)
        return cls.objects.create(
            user=user,
            otp_code=cls.generate_code(),
            expires_at=timezone.now() + timedelta(minutes=validity),
        )

    def is_valid(self):
        return not self.is_used and self.expires_at >= timezone.now()
