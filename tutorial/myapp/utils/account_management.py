"""User management for group admins (teachers) and the global admin (issue #100).

Business logic only — no request handling — so it can be used from views,
middleware, the management command and tests alike.
"""
import csv
import io
import os
import re
import secrets
import shutil
import time
import zipfile
from dataclasses import dataclass, field
from datetime import datetime

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from myapp.models import AccountPrefix, AccountProfile, ZippedFolder, get_profile
from myapp.utils.directories import (
    REVIEW_ROOT,
    REVIEW_SOURCE_MARKER,
    USER_DB_ROOT,
    get_review_directory,
    get_user_home_directory,
)
from myapp.utils.roles import (
    GLOBAL_ADMIN_USERNAME,
    GROUP_ADMIN_GROUP,
    is_global_admin,
    is_group_admin,
)

PREFIX_RE = re.compile(r'^[a-z0-9]{1,16}$')
ACCOUNT_SUFFIX = '_admin'
MAX_USERNAME_LENGTH = 150
MAX_BATCH_SIZE = 200          # sanity limit per create request (typo guard, not a quota)
SCHEDULE_INTERVAL_SECONDS = 60
DELETE_CONFIRMATION = 'LÖSCHEN'

# Short, unambiguous German words (no umlauts) for readable generated passwords.
PASSWORD_WORDS = (
    'apfel', 'ast', 'bach', 'ball', 'baum', 'berg', 'birne', 'blatt', 'blume', 'boot',
    'brot', 'buch', 'burg', 'dach', 'dorf', 'eiche', 'eimer', 'ente', 'feder', 'feld',
    'fisch', 'flagge', 'fluss', 'fuchs', 'gabel', 'garten', 'gras', 'hafen', 'hase', 'haus',
    'hecke', 'held', 'himmel', 'honig', 'hut', 'igel', 'insel', 'jacke', 'kabel', 'kanu',
    'karte', 'katze', 'kerze', 'kiste', 'klee', 'koffer', 'krone', 'kugel', 'lampe', 'leiter',
    'linde', 'loewe', 'mantel', 'markt', 'maus', 'meer', 'mond', 'nebel', 'nest', 'nudel',
    'ofen', 'onkel', 'palme', 'papier', 'pilz', 'pinsel', 'quelle', 'rabe', 'regen', 'riese',
    'robbe', 'rose', 'sack', 'salz', 'sand', 'schaf', 'seil', 'sonne', 'stern', 'stuhl',
    'tafel', 'tanne', 'tasche', 'teller', 'tiger', 'tisch', 'tomate', 'turm', 'ufer', 'uhr',
    'vogel', 'wagen', 'wald', 'wolke', 'wurm', 'zange', 'zebra', 'zelt', 'ziege', 'zug',
)

UNCHANGED = object()


class AccountManagementError(Exception):
    pass


# --------------------------------------------------------------------------------------
# Names and prefixes
# --------------------------------------------------------------------------------------

_UMLAUTS = str.maketrans({'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss'})


def slugify_name(name: str) -> str:
    """'Gruppe 1' -> 'gruppe-1'. Only [a-z0-9-]; '_' is reserved (it separates the data folder)."""
    s = (name or '').strip().lower().translate(_UMLAUTS)
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return s.strip('-')


def normalize_prefix(prefix) -> str:
    return (prefix or '').strip().lower().translate(_UMLAUTS)


def build_base(prefix, slug) -> str:
    """The data-folder name of an account: '<prefix>-<slug>' or '<slug>'."""
    return f"{prefix}-{slug}" if prefix else slug


def username_for(base) -> str:
    return f"{base}{ACCOUNT_SUFFIX}"


def _folder_exists(base) -> bool:
    return os.path.exists(get_user_home_directory(base))


def _folders_starting_with(start) -> bool:
    if not os.path.isdir(USER_DB_ROOT):
        return False
    start = start.lower()
    return any(entry.lower().startswith(start) for entry in os.listdir(USER_DB_ROOT))


def _foreign_prefix_owner(actor, base):
    """If `base` lies in a prefix namespace claimed by someone else, return that prefix."""
    if '-' not in base:
        return None
    first = base.split('-', 1)[0]
    claimed = AccountPrefix.objects.filter(name=first).first()
    if claimed and (actor is None or claimed.owner_id != actor.pk):
        return claimed
    return None


def is_base_available(actor, base) -> bool:
    """A data-folder name is free if no account uses it (as '<base>' or '<base>_…'),
    no folder with that name exists, and it is not inside someone else's prefix."""
    if not base or base.startswith('~'):
        return False
    if User.objects.filter(username__iexact=base).exists():
        return False
    if User.objects.filter(username__istartswith=f"{base}_").exists():
        return False
    if _folder_exists(base):
        return False
    if _foreign_prefix_owner(actor, base) is not None:
        return False
    return True


def suggest_free_base(actor, base, taken=()) -> str:
    """Next free '<base>-N', or '' if there is none (e.g. the base lies in someone else's prefix)."""
    if _foreign_prefix_owner(actor, base) is not None:
        return ''
    for n in range(2, 1000):
        candidate = f"{base}-{n}"
        if candidate not in taken and is_base_available(actor, candidate):
            return candidate
    return ''


@dataclass
class PrefixCheck:
    prefix: str
    valid: bool
    free: bool
    owned_by_me: bool
    message: str
    suggestion: str = ''


def _prefix_namespace_used(prefix) -> bool:
    """Legacy accounts or folders already starting with '<prefix>-'."""
    return (
        User.objects.filter(username__istartswith=f"{prefix}-").exists()
        or _folders_starting_with(f"{prefix}-")
    )


def _prefix_is_free(actor, prefix) -> bool:
    claimed = AccountPrefix.objects.filter(name=prefix).first()
    if claimed:
        return claimed.owner_id == actor.pk
    return not _prefix_namespace_used(prefix)


def suggest_free_prefix(actor, prefix) -> str:
    stem = prefix[:14]
    for n in range(2, 1000):
        candidate = f"{stem}{n}"[:16]
        if _prefix_is_free(actor, candidate):
            return candidate
    return ''


def check_prefix(actor, prefix) -> PrefixCheck:
    prefix = normalize_prefix(prefix)
    if not prefix:
        return PrefixCheck(prefix, True, True, False, 'Kein Präfix: die Namen werden so verwendet, wie sie eingegeben werden.')
    if not PREFIX_RE.match(prefix):
        return PrefixCheck(prefix, False, False, False,
                           'Ein Präfix darf nur aus Kleinbuchstaben und Ziffern bestehen (max. 16 Zeichen).')
    claimed = AccountPrefix.objects.filter(name=prefix).first()
    if claimed and claimed.owner_id == actor.pk:
        return PrefixCheck(prefix, True, True, True, f'Das Präfix „{prefix}“ gehört dir.')
    if claimed or _prefix_namespace_used(prefix):
        suggestion = suggest_free_prefix(actor, prefix)
        return PrefixCheck(prefix, True, False, False,
                           f'Das Präfix „{prefix}“ ist bereits vergeben.'
                           + (f' Vorschlag: „{suggestion}“' if suggestion else ''),
                           suggestion)
    return PrefixCheck(prefix, True, True, False, f'Das Präfix „{prefix}“ ist frei.')


def claim_prefix(actor, prefix) -> AccountPrefix:
    """Claim `prefix` for `actor` (or reuse it if `actor` already owns it)."""
    result = check_prefix(actor, prefix)
    if not result.valid or not result.free:
        raise AccountManagementError(result.message)
    try:
        with transaction.atomic():
            obj, _ = AccountPrefix.objects.get_or_create(name=result.prefix, defaults={'owner': actor})
    except IntegrityError:
        obj = AccountPrefix.objects.filter(name=result.prefix).first()
    if obj is None or obj.owner_id != actor.pk:
        raise AccountManagementError(f'Das Präfix „{result.prefix}“ ist bereits vergeben.')
    return obj


def release_unused_prefixes() -> int:
    """Prefixes without accounts are released so they can be used again (e.g. next term)."""
    deleted, _ = AccountPrefix.objects.filter(accounts__isnull=True).delete()
    return deleted


def expand_series(base_name, count) -> list:
    """('gruppe', 12) -> ['gruppe01', …, 'gruppe12']."""
    width = len(str(count))
    return [f"{base_name}{i:0{width}d}" for i in range(1, count + 1)]


# --------------------------------------------------------------------------------------
# Passwords
# --------------------------------------------------------------------------------------

def generate_password() -> str:
    """Readable password, e.g. 'tiger-wolke-472'."""
    w1 = secrets.choice(PASSWORD_WORDS)
    w2 = secrets.choice(PASSWORD_WORDS)
    return f"{w1}-{w2}-{secrets.randbelow(900) + 100}"


def validate_shared_password(password):
    """Returns a list of error messages (empty if fine)."""
    try:
        validate_password(password)
    except ValidationError as e:
        return list(e.messages)
    return []


# --------------------------------------------------------------------------------------
# Creating accounts
# --------------------------------------------------------------------------------------

@dataclass
class CreateResult:
    created: list = field(default_factory=list)   # [(username, password)]
    errors: list = field(default_factory=list)
    prefix: str = ''
    prefix_suggestion: str = ''

    @property
    def ok(self):
        return not self.errors


def _validate_future(value, label, now, errors):
    if value is not None and value <= now:
        errors.append(f'„{label}“ muss in der Zukunft liegen.')


def create_accounts(actor, names, prefix=None, shared_password=None, delete_at=None, lock_at=None) -> CreateResult:
    """Create '<prefix>-<name>_admin' accounts managed by `actor`.

    Validates everything first and creates nothing if anything is wrong.
    Accounts created by the global admin are independent (no supervising group admin).
    """
    result = CreateResult()
    if not (is_global_admin(actor) or is_group_admin(actor)):
        result.errors.append('Keine Berechtigung, Accounts anzulegen.')
        return result

    now = timezone.now()
    _validate_future(delete_at, 'Automatisch löschen am', now, result.errors)
    _validate_future(lock_at, 'Sperren am', now, result.errors)

    prefix = normalize_prefix(prefix)
    result.prefix = prefix
    if prefix:
        check = check_prefix(actor, prefix)
        if not check.valid or not check.free:
            result.errors.append(check.message)
            result.prefix_suggestion = check.suggestion

    if shared_password:
        result.errors += [f'Gemeinsames Passwort: {m}' for m in validate_shared_password(shared_password)]

    names = [n for n in (names or []) if n and n.strip()]
    if not names:
        result.errors.append('Bitte mindestens einen Namen angeben.')
    if len(names) > MAX_BATCH_SIZE:
        result.errors.append(f'Höchstens {MAX_BATCH_SIZE} Accounts auf einmal.')

    bases = []
    seen = set()
    for raw in names:
        slug = slugify_name(raw)
        if not slug:
            result.errors.append(f'„{raw}“ ist kein gültiger Name (erlaubt: Buchstaben, Ziffern, Bindestrich).')
            continue
        base = build_base(prefix, slug)
        username = username_for(base)
        if len(username) > MAX_USERNAME_LENGTH:
            result.errors.append(f'„{raw}“ ist zu lang.')
            continue
        if base in seen:
            result.errors.append(f'„{username}“ kommt mehrfach vor.')
            continue
        seen.add(base)
        # Name checks are only meaningful once the prefix itself is usable.
        if not result.prefix_suggestion and not is_base_available(actor, base):
            foreign = _foreign_prefix_owner(actor, base)
            if foreign is not None:
                result.errors.append(f'„{username}“ liegt im Präfix „{foreign.name}“, das jemand anderem gehört.')
                continue
            suggestion = suggest_free_base(actor, base, taken=seen)
            hint = f' Vorschlag: „{username_for(suggestion)}“' if suggestion else ''
            result.errors.append(f'„{username}“ ist bereits vergeben.{hint}')
            continue
        bases.append(base)

    if result.errors:
        return result

    managed_by = None if is_global_admin(actor) else actor
    try:
        with transaction.atomic():
            prefix_obj = claim_prefix(actor, prefix) if prefix else None
            for base in bases:
                username = username_for(base)
                password = shared_password or generate_password()
                user = User.objects.create_user(username=username, password=password)
                profile = get_profile(user)
                profile.managed_by = managed_by
                profile.prefix = prefix_obj
                profile.delete_at = delete_at
                profile.lock_at = lock_at
                profile.save()
                result.created.append((username, password))
    except (AccountManagementError, IntegrityError) as e:
        result.created = []
        result.errors.append(str(e) if isinstance(e, AccountManagementError)
                             else 'Ein Name wurde gerade von jemand anderem vergeben. Bitte erneut versuchen.')
        return result

    for username, _ in result.created:
        os.makedirs(get_user_home_directory(username), exist_ok=True)
    return result


# --------------------------------------------------------------------------------------
# Sessions, locking, dates, passwords
# --------------------------------------------------------------------------------------

def get_online_user_ids() -> set:
    """IDs of users with a non-expired session."""
    ids = set()
    for session in Session.objects.filter(expire_date__gte=timezone.now()):
        try:
            uid = session.get_decoded().get('_auth_user_id')
        except Exception:
            continue
        if uid:
            ids.add(str(uid))
    return ids


def end_sessions(users, reason=None) -> int:
    """Delete every session of the given users and log a forced logout for each."""
    by_id = {str(u.pk): u for u in users}
    if not by_id:
        return 0
    ended = 0
    for session in Session.objects.all():
        try:
            data = session.get_decoded()
        except Exception:
            continue
        uid = data.get('_auth_user_id')
        if uid is None or str(uid) not in by_id:
            continue
        if reason:
            _log_forced_logout(by_id[str(uid)], data, reason)
        session.delete()
        ended += 1
    return ended


def _log_forced_logout(user, session_data, reason):
    try:
        from myapp.utils.audit import log_audit_event
        mock_request = type('MockRequest', (), {'session': session_data, 'META': {}})()
        log_audit_event(user, 'FORCED_LOGOUT', mock_request, reason)
    except Exception as e:
        print(f"Audit log for forced logout failed: {e}")


def lock_accounts(users, reason='Account gesperrt') -> int:
    users = list(users)
    ids = [u.pk for u in users]
    User.objects.filter(pk__in=ids).update(is_active=False)
    AccountProfile.objects.filter(user_id__in=ids).update(lock_at=None)
    end_sessions(users, reason)
    return len(ids)


def unlock_accounts(users) -> int:
    ids = [u.pk for u in users]
    return User.objects.filter(pk__in=ids).update(is_active=True)


def set_dates(users, delete_at=UNCHANGED, lock_at=UNCHANGED) -> int:
    changes = {}
    if delete_at is not UNCHANGED:
        changes['delete_at'] = delete_at
    if lock_at is not UNCHANGED:
        changes['lock_at'] = lock_at
    ids = [u.pk for u in users]
    if not changes or not ids:
        return 0
    for u in users:  # make sure every account has a profile
        get_profile(u)
    return AccountProfile.objects.filter(user_id__in=ids).update(**changes)


def reset_passwords(users, shared_password=None) -> list:
    created = []
    for user in users:
        password = shared_password or generate_password()
        user.set_password(password)
        user.save(update_fields=['password'])
        created.append((user.username, password))
    end_sessions(users, 'Passwort zurückgesetzt')
    return created


def set_group_admin(user, enabled: bool):
    from django.contrib.auth.models import Group
    group, _ = Group.objects.get_or_create(name=GROUP_ADMIN_GROUP)
    if enabled:
        user.groups.add(group)
        # A group admin is never supervised by another group admin.
        AccountProfile.objects.filter(user=user).update(managed_by=None)
    else:
        user.groups.remove(group)
    if hasattr(user, '_is_group_admin'):
        del user._is_group_admin


# --------------------------------------------------------------------------------------
# Deleting accounts
# --------------------------------------------------------------------------------------

def _remove_directory(path):
    """rmtree, but only strictly inside user_databases/."""
    root = os.path.realpath(USER_DB_ROOT)
    target = os.path.realpath(path)
    if target == root or not target.startswith(root + os.sep):
        raise AccountManagementError(f'Ungültiger Ordner: {path}')
    if os.path.isdir(target):
        shutil.rmtree(target)


def _remove_review_copies_of(user_id):
    """Remove every review slot that holds a copy of `user_id`'s project."""
    if not os.path.isdir(REVIEW_ROOT):
        return
    for entry in os.listdir(REVIEW_ROOT):
        marker = os.path.join(REVIEW_ROOT, entry, REVIEW_SOURCE_MARKER)
        try:
            with open(marker, 'r', encoding='utf-8') as f:
                source_id = f.read().strip()
        except OSError:
            continue
        if source_id == str(user_id):
            _remove_directory(os.path.join(REVIEW_ROOT, entry))


def accounts_affected_by_deletion(user) -> list:
    """`user`, accounts sharing its data folder, and (for group admins) all managed accounts, recursively."""
    affected = []
    seen = set()

    def visit(u):
        if u.pk in seen:
            return
        seen.add(u.pk)
        affected.append(u)
        base = get_user_home_directory(u.username).rstrip('/').split('/')[-1]
        for sibling in User.objects.filter(username__istartswith=f"{base}_").exclude(pk=u.pk):
            visit(sibling)
        for managed in User.objects.filter(profile__managed_by=u):
            visit(managed)

    visit(user)
    return affected


def delete_accounts(users, actor=None) -> list:
    """Delete accounts without leaving data behind (login audit logs are kept on purpose).

    Deleting a group admin also deletes every account they manage.
    Returns the deleted usernames.
    """
    from axes.models import AccessAttempt

    to_delete = []
    seen = set()
    for user in users:
        for u in accounts_affected_by_deletion(user):
            if u.pk not in seen:
                seen.add(u.pk)
                to_delete.append(u)

    protected = {GLOBAL_ADMIN_USERNAME}
    if actor is not None:
        protected.add(actor.username)
        actor_home = get_user_home_directory(actor.username)
    else:
        actor_home = None
    for u in to_delete:
        if u.username in protected:
            raise AccountManagementError(f'„{u.username}“ kann hier nicht gelöscht werden.')
        if actor_home and get_user_home_directory(u.username) == actor_home:
            raise AccountManagementError(f'„{u.username}“ teilt sich den Datenordner mit deinem Account.')

    deleted = []
    for u in to_delete:
        end_sessions([u])
        home = get_user_home_directory(u.username)
        _remove_directory(home)
        _remove_directory(get_review_directory(u.pk))  # the account's own review slot (if it reviewed others)
        _remove_review_copies_of(u.pk)                  # copies of this account in other reviewers' slots
        for zipped in ZippedFolder.objects.filter(name=home):
            try:
                zipped.zip_file.delete(save=False)
            except Exception:
                pass
            zipped.delete()
        AccessAttempt.objects.filter(username=u.username).delete()
        deleted.append(u.username)
        u.delete()  # profile is removed by CASCADE; AuditLog rows keep the username

    release_unused_prefixes()
    return deleted


# --------------------------------------------------------------------------------------
# Export
# --------------------------------------------------------------------------------------

def _fmt(dt):
    return timezone.localtime(dt).strftime('%Y-%m-%d %H:%M') if dt else ''


def export_accounts_zip(users) -> bytes:
    """One folder per account (its data folder) plus accounts.csv."""
    memory_file = io.BytesIO()
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer, delimiter=';')
    writer.writerow(['username', 'kurs', 'betreut_von', 'erstellt', 'gesperrt', 'sperren_am', 'loeschen_am'])

    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        written_folders = set()
        for user in users:
            profile = get_profile(user)
            writer.writerow([
                user.username,
                profile.prefix.name if profile.prefix else '',
                profile.managed_by.username if profile.managed_by else '',
                _fmt(profile.created_at),
                'ja' if not user.is_active else 'nein',
                _fmt(profile.lock_at),
                _fmt(profile.delete_at),
            ])
            home = get_user_home_directory(user.username)
            folder = home.rstrip('/').split('/')[-1]
            if folder in written_folders or not os.path.isdir(home):
                continue
            written_folders.add(folder)
            for root, _dirs, files in os.walk(home):
                for name in files:
                    if name == 'lockfile':
                        continue
                    abs_path = os.path.join(root, name)
                    rel = os.path.relpath(abs_path, start=home)
                    zipf.write(abs_path, arcname=f"{folder}/{rel}")
        zipf.writestr('accounts.csv', '﻿' + csv_buffer.getvalue())
    return memory_file.getvalue()


# --------------------------------------------------------------------------------------
# Review slot
# --------------------------------------------------------------------------------------

def _wait_for_lockfile(directory, timeout=5.0):
    lockfile = os.path.join(directory, 'lockfile')
    deadline = time.monotonic() + timeout
    while os.path.exists(lockfile) and time.monotonic() < deadline:
        time.sleep(0.1)


def start_review(actor, source):
    """Copy `source`'s project into `actor`'s review slot (replacing the previous review copy).
    The source project and the actor's own project are never touched."""
    src = get_user_home_directory(source.username)
    dst = get_review_directory(actor.pk)
    if os.path.isdir(src):
        _wait_for_lockfile(src)
    if os.path.isdir(dst):
        _remove_directory(dst)
    if os.path.isdir(src):
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns('lockfile'))
    else:
        os.makedirs(dst, exist_ok=True)
    with open(os.path.join(dst, REVIEW_SOURCE_MARKER), 'w', encoding='utf-8') as f:
        f.write(str(source.pk))
    return dst


# --------------------------------------------------------------------------------------
# Schedules (automatic lock / deletion)
# --------------------------------------------------------------------------------------

def apply_schedules(now=None) -> dict:
    """Lock and delete accounts whose scheduled time has passed."""
    now = now or timezone.now()
    due_delete = list(User.objects.filter(profile__delete_at__lte=now).exclude(username=GLOBAL_ADMIN_USERNAME))
    deleted = delete_accounts(due_delete) if due_delete else []
    due_lock = list(User.objects.filter(profile__lock_at__lte=now))
    locked = lock_accounts(due_lock, 'Automatisch gesperrt') if due_lock else 0
    released = release_unused_prefixes()
    return {'deleted': len(deleted), 'locked': locked, 'released_prefixes': released}


def maybe_apply_schedules():
    """apply_schedules(), at most once per SCHEDULE_INTERVAL_SECONDS (cheap to call on every request)."""
    key = 'account_schedules_last_run'
    last = cache.get(key)
    now = time.time()
    if last is not None and now - last < SCHEDULE_INTERVAL_SECONDS:
        return None
    cache.set(key, now, SCHEDULE_INTERVAL_SECONDS * 2)
    return apply_schedules()


def account_is_due(user, now=None) -> bool:
    """True if `user` must not stay logged in (locked, deleted, or a scheduled time has passed)."""
    now = now or timezone.now()
    fresh = User.objects.filter(pk=user.pk).values('is_active', 'profile__lock_at', 'profile__delete_at').first()
    if fresh is None or not fresh['is_active']:
        return True
    for key in ('profile__lock_at', 'profile__delete_at'):
        if fresh[key] is not None and fresh[key] <= now:
            return True
    return False


def parse_local_datetime(value):
    """Parse an <input type="datetime-local"> value in the server's time zone. '' -> None."""
    value = (value or '').strip()
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        raise AccountManagementError(f'Ungültiges Datum: {value}')
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt
