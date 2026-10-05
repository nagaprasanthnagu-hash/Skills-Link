"""
Custom context processor (Section 56.7 of the PRD).

Injects the current user's role and an unread-notification / actionable-item
counter into every template, so individual views never have to repeat this
query logic.
"""


def role_context(request):
    context = {
        'user_role': None,
        'pending_action_count': 0,
    }
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return context

    profile = getattr(user, 'userprofile', None)
    role = profile.role if profile else None
    context['user_role'] = role

    if role == 'customer':
        from apps.bookings.models import Booking
        customer_profile = getattr(user, 'customer_profile', None)
        if customer_profile:
            context['pending_action_count'] = Booking.objects.filter(
                customer=customer_profile,
                status__in=['pending', 'accepted', 'in_progress'],
            ).count()
    elif role == 'provider':
        from apps.bookings.models import Booking
        provider_profile = getattr(user, 'provider_profile', None)
        if provider_profile:
            context['pending_action_count'] = Booking.objects.filter(
                category=provider_profile.category,
                status='pending',
            ).count()
    elif role == 'admin':
        from apps.bookings.models import Booking
        context['pending_action_count'] = Booking.objects.filter(status='pending').count()

    return context
