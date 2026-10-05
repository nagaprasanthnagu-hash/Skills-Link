from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.accounts.models import UserProfile


@receiver(post_save, sender=User)
def ensure_admin_profile(sender, instance, created, **kwargs):
    """
    A superuser created via `createsuperuser` (or the Django admin) has no
    UserProfile, since registration normally creates one explicitly with a
    Customer/Provider role choice. This signal backfills an 'admin' role
    profile so such accounts still redirect correctly after login
    (FR-A3) and pass RoleRequiredMixin checks.
    """
    if instance.is_superuser and not hasattr(instance, 'userprofile'):
        UserProfile.objects.create(
            user=instance,
            full_name=instance.get_full_name() or instance.username,
            role=UserProfile.ROLE_ADMIN,
        )
