from django.core.exceptions import ValidationError
from django.db import models


class Booking(models.Model):
    """Core transactional entity — the central hub of the schema (Section 24, 58.5)."""
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    customer = models.ForeignKey(
        'customers.CustomerProfile', on_delete=models.CASCADE, related_name='bookings',
    )
    provider = models.ForeignKey(
        'providers.ProviderProfile', on_delete=models.SET_NULL, related_name='bookings',
        null=True, blank=True,
    )
    category = models.ForeignKey(
        'categories.ServiceCategory', on_delete=models.PROTECT, related_name='bookings',
    )
    preferred_datetime = models.DateTimeField()
    address = models.TextField()
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['customer']),
            models.Index(fields=['provider']),
        ]

    def __str__(self):
        return f'Booking #{self.id} — {self.category.name} ({self.get_status_display()})'

    def clean(self):
        from django.utils import timezone
        if self.preferred_datetime and self.preferred_datetime < timezone.now() and self._state.adding:
            raise ValidationError({'preferred_datetime': 'Please choose a future date and time.'})

    @property
    def is_cancellable(self):
        return self.status in [self.STATUS_PENDING, self.STATUS_ACCEPTED]

    @property
    def has_review(self):
        return hasattr(self, 'review')


class BookingStatusLog(models.Model):
    """Append-only audit trail of every status transition (Section 24, 44, 58.6)."""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='status_logs')
    old_status = models.CharField(max_length=20, null=True, blank=True)
    new_status = models.CharField(max_length=20)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Booking Status Log'
        verbose_name_plural = 'Booking Status Logs'
        ordering = ['-changed_at']
        indexes = [models.Index(fields=['booking'])]

    def __str__(self):
        return f'Booking #{self.booking_id}: {self.old_status or "created"} -> {self.new_status}'
