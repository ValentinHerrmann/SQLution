"""Accountverwaltung: account management for group admins (teachers) and the global admin (issue #100)."""
from datetime import datetime

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
from myapp.utils.roles import (
    GLOBAL_ADMIN_USERNAME,
    GROUP_ADMIN_GROUP,
    can_manage_accounts,
    is_global_admin,
    managed_queryset,
)

PAGE = 'user_management'
CREATE_FORM_FIELDS = ('prefix', 'mode', 'names', 'series_base', 'series_count', 'delete_at', 'lock_at')


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
        cascade = []
        if user.pk in group_admin_ids:
            cascade = [u.username for u in am.accounts_affected_by_deletion(user) if u.pk != user.pk]
        rows.append({
            'user': user,
            'profile': profile,
            'prefix': profile.prefix.name if profile.prefix else '',
            'online': str(user.pk) in online,
            'is_group_admin': user.pk in group_admin_ids,
            'cascade': cascade,
        })

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
        'max_batch': am.MAX_BATCH_SIZE,
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
        base = post.get('series_base', '').strip()
        try:
            count = int(post.get('series_count', '0'))
        except ValueError:
            count = 0
        if not base or count < 1:
            messages.error(request, 'Bitte einen Basisnamen und eine Anzahl ≥ 1 angeben.')
            return redirect(PAGE)
        if count > am.MAX_BATCH_SIZE:
            messages.error(request, f'Höchstens {am.MAX_BATCH_SIZE} Accounts auf einmal.')
            return redirect(PAGE)
        names = am.expand_series(base, count)
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


@login_required
@user_passes_test(can_manage_accounts)
@require_POST
@csrf_protect
def bulk_action(request):
    action = request.POST.get('action', '')
    users = _resolve_targets(request)
    if not users:
        messages.error(request, 'Keine Accounts ausgewählt.')
        return redirect(PAGE)

    try:
        if action == 'lock':
            am.lock_accounts(users, f'Gesperrt von {request.user.username}')
            messages.success(request, f'{len(users)} Account(s) gesperrt.')
        elif action == 'unlock':
            am.unlock_accounts(users)
            messages.success(request, f'{len(users)} Account(s) entsperrt.')
        elif action == 'set_dates':
            changes = {}
            for key in ('delete_at', 'lock_at'):
                if request.POST.get(f'clear_{key}'):
                    changes[key] = None
                elif request.POST.get(f'bulk_{key}'):
                    value = am.parse_local_datetime(request.POST.get(f'bulk_{key}'))
                    if value <= timezone.now():
                        raise am.AccountManagementError('Das Datum muss in der Zukunft liegen.')
                    changes[key] = value
            if not changes:
                messages.info(request, 'Keine Änderung angegeben.')
            else:
                am.set_dates(users, **changes)
                messages.success(request, f'Termine für {len(users)} Account(s) aktualisiert.')
        elif action == 'reset_password':
            shared = request.POST.get('shared_password', '') or None
            if shared:
                errors = am.validate_shared_password(shared)
                if errors:
                    for e in errors:
                        messages.error(request, f'Gemeinsames Passwort: {e}')
                    return redirect(PAGE)
            _store_passwords(request, am.reset_passwords(users, shared))
            messages.success(request, f'Passwörter für {len(users)} Account(s) zurückgesetzt.')
        elif action == 'download':
            data = am.export_accounts_zip(users)
            response = HttpResponse(data, content_type='application/zip')
            stamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
            response['Content-Disposition'] = f'attachment; filename="accounts_{stamp}.zip"'
            return response
        elif action == 'delete':
            if request.POST.get('confirm', '').strip() != am.DELETE_CONFIRMATION:
                messages.error(request, f'Zum Löschen bitte „{am.DELETE_CONFIRMATION}“ eingeben.')
                return redirect(PAGE)
            deleted = am.delete_accounts(users, actor=request.user)
            messages.success(request, f'{len(deleted)} Account(s) samt Daten gelöscht: {", ".join(deleted)}')
        else:
            messages.error(request, 'Unbekannte Aktion.')
    except am.AccountManagementError as e:
        messages.error(request, str(e))
    return redirect(PAGE)


@login_required
@user_passes_test(can_manage_accounts)
@require_POST
@csrf_protect
def start_review(request, user_id):
    source = get_object_or_404(managed_queryset(request.user), pk=user_id)
    am.start_review(request.user, source)
    request.session['review'] = {'source_id': source.pk, 'source_username': source.username}
    return redirect('overview')


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
