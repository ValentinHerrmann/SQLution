"""Nutzer & Freigaben: db-admins manage their db-users (issue #74) and which queries they see (issue #76)."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from myapp.utils import account_management as am
from myapp.utils import db_users as du
from myapp.utils import query_access as qa
from myapp.utils.directories import get_user_directory
from myapp.utils.roles import can_manage_db_users

PAGE = 'db_users'


def _matrix(directory, names):
    """{category: [{'name': query, 'label': name without category, 'all': bool, 'cells': [{'user': short name, 'checked': bool}]}]}

    Same grouping as on the Nutzerfunktionen page: 'Kategorie - Name'.
    """
    access = qa.load_access(directory)
    matrix = {}
    for query in qa.list_queries(directory):
        value = access.get(query)
        category, label = qa.split_category(query)
        matrix.setdefault(category, []).append({
            'name': query,
            'label': label,
            'all': value == qa.ALL,
            'cells': [{'user': n, 'checked': isinstance(value, list) and n in value} for n in names],
        })
    return matrix


@login_required
@user_passes_test(can_manage_db_users)
def db_users(request):
    admin = request.user
    online = am.get_online_user_ids()
    rows = [{
        'user': u,
        'name': du.short_name(u),
        'online': str(u.pk) in online,
    } for u in du.db_users_of(admin).order_by('username')]
    names = [r['name'] for r in rows]

    return render(request, 'db_users.html', {
        'rows': rows,
        'names': names,
        'matrix': _matrix(get_user_directory(admin.username), names),
        'all_value': qa.ALL,
        'login_prefix': f"{du.base_of(admin)}_",
        'new_passwords': request.session.pop('new_passwords', None),
        'delete_confirmation': am.DELETE_CONFIRMATION,
        'max_users': du.MAX_DB_USERS_PER_PROJECT,
    })


@login_required
@user_passes_test(can_manage_db_users)
@require_POST
@csrf_protect
def create_view(request):
    names = [line.strip() for line in request.POST.get('names', '').splitlines()]
    result = du.create_db_users(request.user, names, request.POST.get('shared_password', '') or None)
    if not result.ok:
        for error in result.errors:
            messages.error(request, error)
        return redirect(PAGE)
    request.session['new_passwords'] = [[u, p] for u, p in result.created]
    messages.success(request, f'{len(result.created)} Nutzer angelegt.')
    return redirect(PAGE)


def _resolve_targets(request):
    """The selected db-users, restricted to those of the current db-admin."""
    ids = {int(i) for i in request.POST.getlist('ids') if str(i).isdigit()}
    return list(du.db_users_of(request.user).filter(pk__in=ids))


def _bulk_lock(request, users):
    am.lock_accounts(users, f'Gesperrt von {request.user.username}')
    messages.success(request, f'{len(users)} Nutzer gesperrt.')


def _bulk_unlock(request, users):
    am.unlock_accounts(users)
    messages.success(request, f'{len(users)} Nutzer entsperrt.')


def _bulk_reset_password(request, users):
    shared = request.POST.get('shared_password', '') or None
    errors = am.validate_shared_password(shared) if shared else []
    if errors:
        for e in errors:
            messages.error(request, f'Gemeinsames Passwort: {e}')
        return
    request.session['new_passwords'] = [[u, p] for u, p in am.reset_passwords(users, shared)]
    messages.success(request, f'Passwörter für {len(users)} Nutzer zurückgesetzt.')


def _bulk_delete(request, users):
    if request.POST.get('confirm', '').strip() != am.DELETE_CONFIRMATION:
        messages.error(request, f'Zum Löschen bitte „{am.DELETE_CONFIRMATION}“ eingeben.')
        return
    deleted = am.delete_accounts(users, actor=request.user)
    messages.success(request, f'{len(deleted)} Nutzer gelöscht. Dein Projekt bleibt unverändert.')


BULK_ACTIONS = {
    'lock': _bulk_lock,
    'unlock': _bulk_unlock,
    'reset_password': _bulk_reset_password,
    'delete': _bulk_delete,
}


@login_required
@user_passes_test(can_manage_db_users)
@require_POST
@csrf_protect
def bulk_action(request):
    handler = BULK_ACTIONS.get(request.POST.get('action', ''))
    if handler is None:
        messages.error(request, 'Unbekannte Aktion.')
        return redirect(PAGE)
    users = _resolve_targets(request)
    if not users:
        messages.error(request, 'Keine Nutzer ausgewählt.')
        return redirect(PAGE)
    try:
        handler(request, users)
    except am.AccountManagementError as e:
        messages.error(request, str(e))
    return redirect(PAGE)


@login_required
@user_passes_test(can_manage_db_users)
@require_POST
@csrf_protect
def save_access(request):
    """Save the matrix. Each ticked box posts 'access' = '<short name or *>:<query>'."""
    directory = get_user_directory(request.user.username)
    queries = set(qa.list_queries(directory))
    names = {du.short_name(u) for u in du.db_users_of(request.user)}

    ticked = {}
    for value in request.POST.getlist('access'):
        who, _, query = value.partition(':')  # short names never contain ':'
        if query in queries and (who == qa.ALL or who in names):
            ticked.setdefault(query, set()).add(who)

    access = {q: qa.ALL if qa.ALL in who else sorted(who) for q, who in ticked.items()}
    qa.save_access(directory, access)
    messages.success(request, 'Freigaben gespeichert.')
    return redirect(PAGE)
