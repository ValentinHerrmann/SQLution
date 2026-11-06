"""Role checks for SQLution accounts.

Kept free of app-model imports so it can be imported from anywhere
(templates' context processor, middleware, decorators).
"""

GLOBAL_ADMIN_USERNAME = 'admin'
GROUP_ADMIN_GROUP = 'Gruppenadmin'


def is_global_admin(user):
    return bool(user and user.is_authenticated and user.username == GLOBAL_ADMIN_USERNAME)


def is_group_admin(user):
    """Group admins (usually teachers) manage the accounts they created."""
    if not (user and user.is_authenticated):
        return False
    cached = getattr(user, '_is_group_admin', None)
    if cached is None:
        cached = user.groups.filter(name=GROUP_ADMIN_GROUP).exists()
        try:
            user._is_group_admin = cached
        except Exception:
            pass
    return cached


def can_manage_accounts(user):
    return is_global_admin(user) or is_group_admin(user)


def is_db_admin(user):
    """Accounts that may edit a database: '<name>_admin' accounts, and group admins while reviewing."""
    if not (user and user.is_authenticated):
        return False
    return user.username.endswith('_admin') or bool(getattr(user, 'in_review', False))


def managed_queryset(actor):
    """All accounts `actor` may manage. Every user-management action resolves its targets through this."""
    from django.contrib.auth.models import User
    if is_global_admin(actor):
        return User.objects.exclude(username=GLOBAL_ADMIN_USERNAME).exclude(pk=actor.pk)
    if is_group_admin(actor):
        return User.objects.filter(profile__managed_by=actor)
    return User.objects.none()
