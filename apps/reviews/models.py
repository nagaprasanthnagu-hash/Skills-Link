from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Review(models.Model):
    """Post-completion rating and feedback, one per booking (Section 25, 58.7)."""
    booking = models.OneToOneField('bookings.Booking', on_delete=models.CASCADE, related_name='review')
    customer = models.ForeignKey('customers.CustomerProfile', on_delete=models.CASCADE, related_name='reviews_given')
    provider = models.ForeignKey('providers.ProviderProfile', on_delete=models.CASCADE, related_name='reviews_received')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['provider'])]

    def __str__(self):
        return f'Review for booking #{self.booking_id} — {self.rating}\u2605'
