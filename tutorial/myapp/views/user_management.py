"""Accountverwaltung: account management for group admins (teachers) and the global admin (issue #100)."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from myapp.models import AccountPrefix, get_profile
from myapp.utils import account_management as am
from myapp.utils.directories import get_user_suffix
from myapp.utils.roles import (
    GLOBAL_ADMIN_USERNAME,
    GROUP_ADMIN_GROUP,
    can_manage_accounts,
    is_global_admin,
    managed_queryset,
)

PAGE = 'user_management'
CREATE_FORM_FIELDS = ('prefix', 'mode', 'names', 'series_base', 'series_first', 'series_last', 'series_digits',
                      'delete_at', 'lock_at')


def _resolve_targets(request):
    """The selected accounts, restricted to those the current user may manage."""
    raw_ids = request.POST.getlist('ids')
    ids = {int(i) for i in raw_ids if str(i).isdigit()}
    users = list(managed_queryset(request.user).filter(pk__in=ids).select_related('profile'))
    dropped = len(ids) - len(users)
    if dropped:
        messages.warning(request, f'{dropped} ausgewählte(r) Account(s) gehören nicht zu deinen Accounts und wurden ignoriert.')
    return users


def _store_passwords(request, created):
    request.session['new_passwords'] = [[u, p] for u, p in created]


@login_required
@user_passes_test(can_manage_accounts)
def user_management(request):
    actor = request.user
    global_admin = is_global_admin(actor)
    online = am.get_online_user_ids()
    accounts = (managed_queryset(actor)
                .select_related('profile', 'profile__managed_by', 'profile__prefix')
                .prefetch_related('groups')
                .order_by('username'))

    group_admin_ids = set(User.objects.filter(groups__name=GROUP_ADMIN_GROUP).values_list('pk', flat=True))
    rows = []
    for user in accounts:
        profile = get_profile(user)
        owns_folder = am.owns_data_folder(user)
        cascade = []
        if user.pk in group_admin_ids or owns_folder:
            cascade = [u.username for u in am.accounts_affected_by_deletion(user) if u.pk != user.pk]
        rows.append({
            'user': user,
            'profile': profile,
            'prefix': profile.prefix.name if profile.prefix else '',
            'online': str(user.pk) in online,
            'is_group_admin': user.pk in group_admin_ids,
            'cascade': cascade,
            'reviewable': profile.managed_by_id == actor.pk,
            # db-users ('<base>_<name>') are listed right below the account whose project they use
            'db_user_of': '' if owns_folder else user.username.split('_', 1)[0],
        })
    rows.sort(key=lambda r: (r['db_user_of'] or r['user'].username.removesuffix(am.ACCOUNT_SUFFIX),
                             r['db_user_of'] != '', r['user'].username))

    if global_admin:
        prefixes = AccountPrefix.objects.select_related('owner').all()
    else:
        prefixes = AccountPrefix.objects.filter(owner=actor)
    last_prefix = AccountPrefix.objects.filter(owner=actor).order_by('-created_at').first()

    form_data = request.session.pop('create_form', None) or {}
    if 'prefix' not in form_data:
        form_data['prefix'] = last_prefix.name if last_prefix else ''

    return render(request, 'user_management.html', {
        'rows': rows,
        'courses': sorted({r['prefix'] for r in rows if r['prefix']}),
        'prefixes': prefixes,
        'is_global': global_admin,
        'new_passwords': request.session.pop('new_passwords', None),
        'form_data': form_data,
        'delete_confirmation': am.DELETE_CONFIRMATION,
        'max_series_digits': am.MAX_SERIES_DIGITS,
        'group_admin_name': GROUP_ADMIN_GROUP,
    })


@login_required
@user_passes_test(can_manage_accounts)
@require_GET
def prefix_check(request):
    result = am.check_prefix(request.user, request.GET.get('prefix', ''))
    return JsonResponse({
        'prefix': result.prefix,
        'valid': result.valid,
        'free': result.free,
        'owned_by_me': result.owned_by_me,
        'message': result.message,
        'suggestion': result.suggestion,
    })


def _int_or_none(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _series_names(post):
    """(names, error) for 'gruppe' von 13 bis 20 (Stellen optional)."""
    base = post.get('series_base', '').strip()
    first = _int_or_none(post.get('series_first') or '1')
    last = _int_or_none(post.get('series_last'))
    digits = _int_or_none(post.get('series_digits')) if post.get('series_digits') else None
    if not base:
        return [], 'Bitte einen Basisnamen angeben.'
    if first is None or last is None or first < 0 or last < first:
        return [], 'Bitte eine gültige Nummer „von“ und „bis“ angeben (bis ≥ von ≥ 0).'
    if post.get('series_digits') and (digits is None or not 1 <= digits <= am.MAX_SERIES_DIGITS):
        return [], f'„Stellen“ muss zwischen 1 und {am.MAX_SERIES_DIGITS} liegen.'
    if last - first + 1 > am.MAX_BATCH_SIZE:
        return [], f'Höchstens {am.MAX_BATCH_SIZE} Accounts auf einmal.'
    return am.expand_series(base, first, last, digits), None


@login_required
@user_passes_test(can_manage_accounts)
@require_POST
@csrf_protect
def create_accounts_view(request):
    post = request.POST
    request.session['create_form'] = {k: post.get(k, '') for k in CREATE_FORM_FIELDS}
    try:
        delete_at = am.parse_local_datetime(post.get('delete_at'))
        lock_at = am.parse_local_datetime(post.get('lock_at'))
    except am.AccountManagementError as e:
        messages.error(request, str(e))
        return redirect(PAGE)

    if post.get('mode') == 'series':
        names, error = _series_names(post)
        if error:
            messages.error(request, error)
            return redirect(PAGE)
    else:
        names = [line.strip() for line in post.get('names', '').splitlines()]

    result = am.create_accounts(
        request.user, names,
        prefix=post.get('prefix', ''),
        shared_password=post.get('shared_password', '') or None,
        delete_at=delete_at,
        lock_at=lock_at,
    )
    if not result.ok:
        for error in result.errors:
            messages.error(request, error)
        return redirect(PAGE)

    request.session.pop('create_form', None)
    _store_passwords(request, result.created)
    messages.success(request, f'{len(result.created)} Account(s) angelegt.')
    return redirect(PAGE)


def _bulk_lock(request, users):
    am.lock_accounts(users, f'Gesperrt von {request.user.username}')
    messages.success(request, f'{len(users)} Account(s) gesperrt.')


def _bulk_unlock(request, users):
    am.unlock_accounts(users)
    messages.success(request, f'{len(users)} Account(s) entsperrt.')


def _requested_date_changes(post) -> dict:
    """{'delete_at': datetime|None, 'lock_at': …} for the fields the user filled in or cleared."""
    changes = {}
    for key in ('delete_at', 'lock_at'):
        if post.get(f'clear_{key}'):
            changes[key] = None
        elif post.get(f'bulk_{key}'):
            value = am.parse_local_datetime(post.get(f'bulk_{key}'))
            if value <= timezone.now():
                raise am.AccountManagementError('Das Datum muss in der Zukunft liegen.')
            changes[key] = value
    return changes


def _bulk_set_dates(request, users):
    changes = _requested_date_changes(request.POST)
    if not changes:
        messages.info(request, 'Keine Änderung angegeben.')
        return
    am.set_dates(users, **changes)
    messages.success(request, f'Termine für {len(users)} Account(s) aktualisiert.')


def _bulk_reset_password(request, users):
    shared = request.POST.get('shared_password', '') or None
    errors = am.validate_shared_password(shared) if shared else []
    if errors:
        for e in errors:
            messages.error(request, f'Gemeinsames Passwort: {e}')
        return
    _store_passwords(request, am.reset_passwords(users, shared))
    messages.success(request, f'Passwörter für {len(users)} Account(s) zurückgesetzt.')


def _bulk_download(request, users):
    response = HttpResponse(am.export_accounts_zip(users), content_type='application/zip')
    stamp = timezone.localtime().strftime('%Y-%m-%d_%H-%M')
    response['Content-Disposition'] = f'attachment; filename="accounts_{stamp}.zip"'
    return response


def _bulk_delete(request, users):
    if request.POST.get('confirm', '').strip() != am.DELETE_CONFIRMATION:
        messages.error(request, f'Zum Löschen bitte „{am.DELETE_CONFIRMATION}“ eingeben.')
        return
    deleted = am.delete_accounts(users, actor=request.user)
    messages.success(request, f'{len(deleted)} Account(s) samt Daten gelöscht: {", ".join(deleted)}')


BULK_ACTIONS = {
    'lock': _bulk_lock,
    'unlock': _bulk_unlock,
    'set_dates': _bulk_set_dates,
    'reset_password': _bulk_reset_password,
    'download': _bulk_download,
    'delete': _bulk_delete,
}


@login_required
@user_passes_test(can_manage_accounts)
@require_POST
@csrf_protect
def bulk_action(request):
    handler = BULK_ACTIONS.get(request.POST.get('action', ''))
    if handler is None:
        messages.error(request, 'Unbekannte Aktion.')
        return redirect(PAGE)
    users = _resolve_targets(request)
    if not users:
        messages.error(request, 'Keine Accounts ausgewählt.')
        return redirect(PAGE)
    try:
        response = handler(request, users)
    except am.AccountManagementError as e:
        messages.error(request, str(e))
        response = None
    return response or redirect(PAGE)


@login_required
@user_passes_test(can_manage_accounts)
@require_POST
@csrf_protect
def start_review(request, user_id):
    """Only the account's own group admin may review it (never the global admin, never independent accounts).

    Reviewing a db-user shows exactly what that db-user sees (its released queries), not the project.
    """
    source = get_object_or_404(User.objects.filter(profile__managed_by=request.user), pk=user_id)
    am.start_review(request.user, source)
    db_user = '' if am.owns_data_folder(source) else get_user_suffix(source.username)
    request.session['review'] = {'source_id': source.pk, 'source_username': source.username, 'db_user': db_user}
    return redirect('user_functions' if db_user else 'overview')


@login_required
@require_POST
@csrf_protect
def exit_review(request):
    request.session.pop('review', None)
    if request.user.username.endswith('_admin'):
        return redirect('overview')
    return redirect(PAGE)


@login_required
@user_passes_test(can_manage_accounts)
@require_POST
@csrf_protect
def set_role(request, user_id):
    if not is_global_admin(request.user):
        return HttpResponseForbidden('Nur der globale Admin kann Rollen vergeben.')
    target = get_object_or_404(User.objects.exclude(username=GLOBAL_ADMIN_USERNAME), pk=user_id)
    enabled = request.POST.get('group_admin') == '1'
    am.set_group_admin(target, enabled)
    if enabled:
        messages.success(request, f'{target.username} ist jetzt Gruppenadmin.')
    else:
        messages.success(request, f'{target.username} ist kein Gruppenadmin mehr. '
                                  'Die zugeordneten Accounts bleiben bestehen.')
    return redirect(PAGE)
