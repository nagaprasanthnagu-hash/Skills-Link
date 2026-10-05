"""
Custom authentication backend (Section 64 of the PRD).

Allows a user to log in with either their username or their registered
email address (FR-A of Section 20), while still relying entirely on
Django's own password hashing and verification — never a hand-rolled
comparison.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()


class EmailOrUsernameModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if username is None or password is None:
            return None

        try:
            user = User.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except User.DoesNotExist:
            # Run the hasher anyway to mitigate username-enumeration via
            # response-time differences.
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            user = User.objects.filter(Q(username__iexact=username) | Q(email__iexact=username)).order_by('id').first()

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
