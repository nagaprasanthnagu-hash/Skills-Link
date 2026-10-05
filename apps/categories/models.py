from django.db import models


class ServiceCategory(models.Model):
    """Master catalogue of home-service categories (Section 21, 58.4)."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Service Category'
        verbose_name_plural = 'Service Categories'
        ordering = ['name']

    def __str__(self):
        return self.name
