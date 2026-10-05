"""
Custom template tags/filters (Section 56.7, Section 70.3 of the PRD).

`status_badge` maps a Booking.status value to the authoritative badge
colour mapping in Section 70.3, so a booking's status is instantly
recognisable by colour on every screen it appears on.
"""
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

# Matches Section 70.3 exactly.
_STATUS_BADGE_MAP = {
    'pending': ('bookinghub-badge-pending', 'Pending'),
    'accepted': ('bookinghub-badge-accepted', 'Accepted'),
    'in_progress': ('bookinghub-badge-in-progress', 'In Progress'),
    'completed': ('bookinghub-badge-completed', 'Completed'),
    'cancelled': ('bookinghub-badge-cancelled', 'Cancelled'),
}


@register.filter(name='status_badge')
def status_badge(status):
    css_class, label = _STATUS_BADGE_MAP.get(status, ('bookinghub-badge-pending', status or 'Unknown'))
    return mark_safe(f'<span class="bookinghub-status-badge {css_class}">{label}</span>')


@register.filter(name='star_range')
def star_range(rating):
    """Returns a range for rendering `rating` filled stars, used in review templates."""
    try:
        return range(int(rating))
    except (TypeError, ValueError):
        return range(0)


@register.filter(name='empty_star_range')
def empty_star_range(rating):
    try:
        return range(5 - int(rating))
    except (TypeError, ValueError):
        return range(5)
