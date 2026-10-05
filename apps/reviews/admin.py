from django.contrib import admin

from apps.reviews.models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('booking', 'customer', 'provider', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('customer__user__username', 'provider__user__username')
