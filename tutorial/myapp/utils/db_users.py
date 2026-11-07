"""db-users managed by their db-admin (issue #74).

A db-admin '<base>_admin' creates db-users '<base>_<name>'. They work on the db-admin's
project (same data folder) and see only the queries released to them (see query_access).
The UI shows the short name '<name>'; the full username is only needed to log in.

Business logic only — no request handling — like account_management.
"""
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction

from myapp.models import get_profile
from myapp.utils import account_management as am
from myapp.utils.directories import get_user_suffix
from myapp.utils.roles import can_manage_db_users

MAX_DB_USERS_PER_PROJECT = 50
RESERVED_NAMES = {'admin'}  # '<base>_admin' is the db-admin itself


def base_of(admin) -> str:
    """'q11inf-gruppe1_admin' -> 'q11inf-gruppe1'."""
    return admin.username[:-len(am.ACCOUNT_SUFFIX)]


def short_name(user) -> str:
    """'q11inf-gruppe1_leser' -> 'leser'."""
    return get_user_suffix(user.username)


def db_users_of(admin):
    """The db-users of `admin`'s project. Every db-user action resolves its targets through this."""
    if not can_manage_db_users(admin):
        return User.objects.none()
    return User.objects.filter(username__startswith=f"{base_of(admin)}_").exclude(pk=admin.pk)


def _name_error(admin, raw, slug, seen):
    """The error message for one requested name, or None if it can be used."""
    if not slug:
        return f'„{raw}“ ist kein gültiger Name (erlaubt: Buchstaben, Ziffern, Bindestrich).'
    if slug in RESERVED_NAMES:
        return f'„{slug}“ ist reserviert.'
    username = f"{base_of(admin)}_{slug}"
    if len(username) > am.MAX_USERNAME_LENGTH:
        return f'„{raw}“ ist zu lang.'
    if slug in seen:
        return f'„{slug}“ kommt mehrfach vor.'
    if User.objects.filter(username__iexact=username).exists():
        return f'„{slug}“ gibt es schon.'
    return None


def _resolve_slugs(admin, names, result):
    """Turn the requested names into short names; errors go into `result`."""
    names = [n.strip() for n in (names or []) if n and n.strip()]
    if not names:
        result.errors.append('Bitte mindestens einen Namen angeben.')
    if db_users_of(admin).count() + len(names) > MAX_DB_USERS_PER_PROJECT:
        result.errors.append(f'Höchstens {MAX_DB_USERS_PER_PROJECT} Nutzer pro Projekt.')
    slugs = []
    seen = set()
    for raw in names:
        slug = am.slugify_name(raw)
        error = _name_error(admin, raw, slug, seen)
        seen.add(slug)
        if error:
            result.errors.append(error)
        else:
            slugs.append(slug)
    return slugs


def _persist_db_users(admin, slugs, shared_password):
    """Create the users in one transaction. They inherit teacher, course and dates from the db-admin."""
    admin_profile = get_profile(admin)
    created = []
    with transaction.atomic():
        for slug in slugs:
            username = f"{base_of(admin)}_{slug}"
            password = shared_password or am.generate_password()
            user = User.objects.create_user(username=username, password=password)
            profile = get_profile(user)
            profile.managed_by = admin_profile.managed_by  # the teacher still sees and manages them
            profile.prefix = admin_profile.prefix
            profile.lock_at = admin_profile.lock_at
            profile.delete_at = admin_profile.delete_at
            profile.save()
            created.append((username, password))
    return created


def create_db_users(admin, names, shared_password=None) -> am.CreateResult:
    """Create '<base>_<name>' db-users for `admin`'s project.

    Validates everything first and creates nothing if anything is wrong.
    """
    result = am.CreateResult()
    if not can_manage_db_users(admin):
        result.errors.append('Keine Berechtigung, Nutzer anzulegen.')
        return result
    if shared_password:
        result.errors += [f'Gemeinsames Passwort: {m}' for m in am.validate_shared_password(shared_password)]
    slugs = _resolve_slugs(admin, names, result)
    if result.errors:
        return result

    try:
        result.created = _persist_db_users(admin, slugs, shared_password)
    except IntegrityError:
        result.errors.append('Ein Name wurde gerade von jemand anderem vergeben. Bitte erneut versuchen.')
    return result
