"""
Service layer centralising the booking status-transition state machine
(Section 24, Section 56.7 of the PRD).

Both the Provider views and any future API layer call these functions
rather than mutating Booking.status directly, so the transition rules and
audit trail (BookingStatusLog) are enforced in exactly one place.
"""
from django.core.exceptions import PermissionDenied
from django.db import transaction

from apps.bookings.models import Booking, BookingStatusLog


class InvalidTransitionError(Exception):
    """Raised when a requested status change is not a permitted forward move."""


# Only these forward moves are permitted (Section 23/24 business rules —
# a provider cannot move a booking backward, or skip an intermediate state).
_ALLOWED_TRANSITIONS = {
    Booking.STATUS_PENDING: {Booking.STATUS_ACCEPTED, Booking.STATUS_CANCELLED},
    Booking.STATUS_ACCEPTED: {Booking.STATUS_IN_PROGRESS, Booking.STATUS_CANCELLED},
    Booking.STATUS_IN_PROGRESS: {Booking.STATUS_COMPLETED},
    Booking.STATUS_COMPLETED: set(),
    Booking.STATUS_CANCELLED: set(),
}


@transaction.atomic
def _transition(booking, new_status):
    old_status = booking.status
    if new_status not in _ALLOWED_TRANSITIONS.get(old_status, set()):
        raise InvalidTransitionError(
            f'Cannot move booking #{booking.id} from {old_status} to {new_status}.'
        )
    booking.status = new_status
    booking.save(update_fields=['status', 'updated_at'])
    BookingStatusLog.objects.create(booking=booking, old_status=old_status, new_status=new_status)
    return booking


@transaction.atomic
def create_booking(customer_profile, category, preferred_datetime, address, description):
    booking = Booking.objects.create(
        customer=customer_profile,
        category=category,
        preferred_datetime=preferred_datetime,
        address=address,
        description=description,
        status=Booking.STATUS_PENDING,
    )
    BookingStatusLog.objects.create(booking=booking, old_status=None, new_status=Booking.STATUS_PENDING)
    return booking


@transaction.atomic
def accept_booking(booking, provider_profile):
    """
    First-come, first-served accept (Section 23 design note): locks the row,
    re-checks the booking is still Pending and matches the provider's
    category, then assigns the provider and transitions to Accepted.
    """
    locked_booking = Booking.objects.select_for_update().get(pk=booking.pk)

    if locked_booking.status != Booking.STATUS_PENDING:
        raise InvalidTransitionError('This booking is no longer available.')

    if not provider_profile.is_active:
        raise PermissionDenied('Your provider account is currently inactive. Contact support to reactivate it.')

    if locked_booking.category_id != provider_profile.category_id:
        provider_category = provider_profile.category.name if provider_profile.category_id else 'not set'
        raise PermissionDenied(
            f'This booking is in "{locked_booking.category}". Your registered category is '
            f'"{provider_category}" — update it from Edit Profile to accept bookings in that category.'
        )

    if not locked_booking.category.is_active:
        raise PermissionDenied('This service category is no longer active.')

    locked_booking.provider = provider_profile
    locked_booking.save(update_fields=['provider'])
    return _transition(locked_booking, Booking.STATUS_ACCEPTED)


@transaction.atomic
def advance_status(booking, provider_profile, new_status):
    if booking.provider_id != provider_profile.id:
        raise PermissionDenied('Only the assigned provider can update this booking.')
    return _transition(booking, new_status)


@transaction.atomic
def cancel_booking(booking, actor_customer_profile):
    if booking.customer_id != actor_customer_profile.id:
        raise PermissionDenied('You may only cancel your own bookings.')
    if not booking.is_cancellable:
        raise InvalidTransitionError('This action is no longer available for this booking.')
    return _transition(booking, Booking.STATUS_CANCELLED)
