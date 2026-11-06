"""Tests for the app-based user management (issue #100).

This module is intentionally named so it is collected before test_coverage.py,
which replaces several myapp modules in sys.modules with stubs at import time.
Everything this module needs is imported here, at collection time.
"""
import io
import os
import zipfile
from datetime import timedelta

import pytest
from django.contrib.auth.models import Group, User
from django.contrib.messages import get_messages
from django.core.cache import cache
from django.db import transaction
from django.test import Client
from django.utils import timezone

import myapp.context_processors  # noqa: F401  (imported early, see module docstring)
import myapp.middleware  # noqa: F401
import myapp.urls  # noqa: F401
from axes.models import AccessAttempt
from myapp.models import AccountPrefix, AccountProfile, AuditLog, get_profile
from myapp.utils import account_management as am
from myapp.utils.directories import (
    REVIEW_SOURCE_MARKER,
    get_review_directory,
    get_user_directory,
    get_user_home_directory,
)
from myapp.utils.roles import GROUP_ADMIN_GROUP

pytestmark = pytest.mark.no_auth_bypass


# --------------------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------------------

@pytest.fixture(scope='module', autouse=True)
def test_database():
    """A fresh in-memory test database for this module (pytest-django is not used)."""
    from django.test.utils import (
        setup_databases,
        setup_test_environment,
        teardown_databases,
        teardown_test_environment,
    )
    env_set_up = False
    try:
        setup_test_environment()
        env_set_up = True
    except RuntimeError:
        pass  # already set up
    old_config = setup_databases(verbosity=0, interactive=False)
    yield
    teardown_databases(old_config, verbosity=0)
    if env_set_up:
        teardown_test_environment()


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    """Each test runs in its own folder (user_databases/ is relative) and DB transaction."""
    monkeypatch.chdir(tmp_path)
    os.makedirs('user_databases')
    cache.clear()
    atomic = transaction.atomic()
    atomic.__enter__()
    try:
        yield tmp_path
    finally:
        transaction.set_rollback(True)
        atomic.__exit__(None, None, None)
        cache.clear()


def make_group_admin(username):
    user = User.objects.create_user(username=username, password='Lehrer-Passwort-123')
    user.groups.add(Group.objects.get_or_create(name=GROUP_ADMIN_GROUP)[0])
    return User.objects.get(pk=user.pk)  # fresh object (no cached role)


@pytest.fixture
def admin():
    return User.objects.create_user(username='admin', password='Admin-Passwort-123')


@pytest.fixture
def teacher():
    return make_group_admin('mueller')


@pytest.fixture
def other_teacher():
    return make_group_admin('schmidt')


def client_for(user):
    c = Client()
    c.force_login(user)
    return c


def create(actor, names, **kwargs):
    result = am.create_accounts(actor, names, **kwargs)
    assert result.ok, result.errors
    return result


def message_texts(response):
    return [str(m) for m in get_messages(response.wsgi_request)]


# --------------------------------------------------------------------------------------
# Naming and prefixes
# --------------------------------------------------------------------------------------

def test_slugify_and_username():
    assert am.slugify_name(' Gruppe Ä_1 ') == 'gruppe-ae-1'
    assert am.username_for(am.build_base('q11inf', 'gruppe1')) == 'q11inf-gruppe1_admin'
    assert am.username_for(am.build_base('', 'gruppe1')) == 'gruppe1_admin'
    assert am.expand_series('gruppe', 12)[:2] == ['gruppe01', 'gruppe02']
    assert am.expand_series('gruppe', 3) == ['gruppe1', 'gruppe2', 'gruppe3']


def test_create_with_prefix(teacher):
    result = create(teacher, ['Gruppe 1', 'gruppe2'], prefix='Q11inf')
    usernames = [u for u, _ in result.created]
    assert usernames == ['q11inf-gruppe-1_admin', 'q11inf-gruppe2_admin']
    passwords = [p for _, p in result.created]
    assert len(set(passwords)) == 2
    for username, password in result.created:
        user = User.objects.get(username=username)
        assert user.check_password(password)
        assert user.profile.managed_by == teacher
        assert user.profile.prefix.name == 'q11inf'
        assert os.path.isdir(get_user_home_directory(username))
    assert AccountPrefix.objects.get(name='q11inf').owner == teacher


def test_shared_password_applies_to_batch(teacher):
    result = create(teacher, am.expand_series('team', 3), prefix='kurs', shared_password='Sonnenblume-2026')
    assert {p for _, p in result.created} == {'Sonnenblume-2026'}


def test_weak_shared_password_rejected(teacher):
    result = am.create_accounts(teacher, ['a'], shared_password='123')
    assert not result.ok
    assert not User.objects.filter(username='a_admin').exists()


def test_collision_with_user_and_folder_is_blocked_with_suggestion(teacher):
    User.objects.create_user(username='gruppe1_admin', password='x')
    os.makedirs('user_databases/gruppe2')
    result = am.create_accounts(teacher, ['gruppe1', 'gruppe2', 'gruppe3'])
    assert not result.ok
    joined = ' '.join(result.errors)
    assert 'gruppe1-2_admin' in joined
    assert 'gruppe2-2_admin' in joined
    # all-or-nothing: gruppe3 was not created either
    assert not User.objects.filter(username='gruppe3_admin').exists()


def test_db_user_account_blocks_its_folder_name(teacher):
    User.objects.create_user(username='projekt_leser', password='x')  # shares folder 'projekt'
    assert not am.is_base_available(teacher, 'projekt')


def test_prefix_claim_reuse_and_block(teacher, other_teacher):
    create(teacher, ['gruppe1'], prefix='q11inf')
    # the owner can add more accounts to the course later
    create(teacher, ['gruppe2'], prefix='q11inf')

    check = am.check_prefix(other_teacher, 'q11inf')
    assert check.valid
    assert not check.free
    assert check.suggestion == 'q11inf2'
    result = am.create_accounts(other_teacher, ['gruppe1'], prefix='q11inf')
    assert not result.ok
    assert result.prefix_suggestion == 'q11inf2'

    # nobody may squat in the claimed namespace without the prefix either
    result = am.create_accounts(other_teacher, ['q11inf-gruppe9'])
    assert not result.ok


def test_legacy_accounts_and_folders_block_prefix(teacher):
    User.objects.create_user(username='abc-team_admin', password='x')
    os.makedirs('user_databases/xyz-team')
    assert not am.check_prefix(teacher, 'abc').free
    assert not am.check_prefix(teacher, 'xyz').free
    assert am.check_prefix(teacher, 'abcd').free


def test_invalid_prefix(teacher):
    check = am.check_prefix(teacher, 'q11-inf')
    assert not check.valid


def test_prefix_released_after_last_account_deleted(teacher, other_teacher):
    result = create(teacher, ['gruppe1'], prefix='q11inf')
    user = User.objects.get(username=result.created[0][0])
    am.delete_accounts([user], actor=teacher)
    assert not AccountPrefix.objects.filter(name='q11inf').exists()
    assert am.check_prefix(other_teacher, 'q11inf').free


def test_dates_must_be_in_future(teacher):
    past = timezone.now() - timedelta(hours=1)
    result = am.create_accounts(teacher, ['a'], lock_at=past)
    assert not result.ok


# --------------------------------------------------------------------------------------
# Permissions / scoping
# --------------------------------------------------------------------------------------

def test_page_access(admin, teacher):
    assert client_for(admin).get('/user_management/').status_code == 200
    response = client_for(teacher).get('/user_management/')
    assert response.status_code == 200
    assert 'Accountverwaltung' in response.content.decode()

    student = User.objects.create_user(username='kid_admin', password='x')
    assert client_for(student).get('/user_management/').status_code == 302


def test_group_admin_cannot_touch_foreign_accounts(teacher, other_teacher):
    own = User.objects.get(username=create(teacher, ['a'], prefix='kursa').created[0][0])
    foreign = User.objects.get(username=create(other_teacher, ['b'], prefix='kursb').created[0][0])
    independent = User.objects.create_user(username='frei_admin', password='x')

    c = client_for(teacher)
    response = c.post('/user_management/bulk/', {'action': 'lock', 'ids': [own.pk, foreign.pk, independent.pk]})
    assert response.status_code == 302
    assert any('ignoriert' in m for m in message_texts(response))
    own.refresh_from_db(); foreign.refresh_from_db(); independent.refresh_from_db()
    assert not own.is_active
    assert foreign.is_active
    assert independent.is_active

    assert c.post(f'/user_management/review/{foreign.pk}/').status_code == 404
    c.post('/user_management/bulk/', {'action': 'delete', 'confirm': am.DELETE_CONFIRMATION, 'ids': [foreign.pk]})
    assert User.objects.filter(pk=foreign.pk).exists()


def test_global_admin_manages_everything(admin, teacher):
    foreign = User.objects.get(username=create(teacher, ['b'], prefix='kursb').created[0][0])
    client_for(admin).post('/user_management/bulk/', {'action': 'lock', 'ids': [foreign.pk]})
    foreign.refresh_from_db()
    assert not foreign.is_active


def test_accounts_created_by_global_admin_are_independent(admin):
    result = create(admin, ['lehrkraft'])
    user = User.objects.get(username=result.created[0][0])
    assert user.profile.managed_by is None


def test_role_toggle_only_for_global_admin(admin, teacher):
    target = User.objects.create_user(username='neu_admin', password='x')
    assert client_for(teacher).post(f'/user_management/role/{target.pk}/', {'group_admin': '1'}).status_code == 403
    client_for(admin).post(f'/user_management/role/{target.pk}/', {'group_admin': '1'})
    assert target.groups.filter(name=GROUP_ADMIN_GROUP).exists()
    client_for(admin).post(f'/user_management/role/{target.pk}/', {'group_admin': '0'})
    assert not target.groups.filter(name=GROUP_ADMIN_GROUP).exists()


def test_prefix_check_endpoint(teacher, other_teacher):
    create(teacher, ['a'], prefix='kurs')
    data = client_for(other_teacher).get('/user_management/prefix-check/', {'prefix': 'kurs'}).json()
    assert data == {**data, 'valid': True, 'free': False, 'suggestion': 'kurs2'}
    data = client_for(teacher).get('/user_management/prefix-check/', {'prefix': 'kurs'}).json()
    assert data['free']
    assert data['owned_by_me']


# --------------------------------------------------------------------------------------
# Create via view, passwords shown once
# --------------------------------------------------------------------------------------

def test_create_view_shows_passwords_once(teacher):
    c = client_for(teacher)
    response = c.post('/user_management/create/', {
        'prefix': 'q11inf', 'mode': 'series', 'series_base': 'gruppe', 'series_count': '3',
        'lock_at': '', 'delete_at': '',
    })
    assert response.status_code == 302
    assert User.objects.filter(username__startswith='q11inf-gruppe').count() == 3
    page = c.get('/user_management/').content.decode()
    assert 'Zugangsdaten' in page
    assert 'q11inf-gruppe1_admin' in page
    assert 'Zugangsdaten' not in c.get('/user_management/').content.decode()


def test_create_view_with_dates(teacher):
    lock = (timezone.localtime() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M')
    client_for(teacher).post('/user_management/create/', {
        'prefix': '', 'mode': 'list', 'names': 'alpha\nbeta', 'lock_at': lock, 'delete_at': '',
    })
    profile = User.objects.get(username='alpha_admin').profile
    assert profile.lock_at is not None
    assert profile.delete_at is None


# --------------------------------------------------------------------------------------
# Deletion
# --------------------------------------------------------------------------------------

def test_delete_removes_everything_but_audit_logs(teacher):
    username = create(teacher, ['gruppe1'], prefix='kurs').created[0][0]
    student = User.objects.get(username=username)
    home = get_user_home_directory(username)
    with open(os.path.join(home, 'abfrage.sql'), 'w') as f:
        f.write('SELECT 1;')
    AuditLog.objects.create(user=student, username=username, action='LOGIN')
    AccessAttempt.objects.create(username=username, ip_address='127.0.0.1', user_agent='x',
                                 failures_since_start=1, get_data='', post_data='', http_accept='', path_info='/')
    student_client = client_for(student)
    am.start_review(teacher, student)
    review_dir = get_review_directory(teacher.pk)
    assert os.path.isdir(review_dir)

    c = client_for(teacher)
    c.post('/user_management/bulk/', {'action': 'delete', 'confirm': 'nein', 'ids': [student.pk]})
    assert User.objects.filter(pk=student.pk).exists()  # wrong confirmation -> nothing happens

    c.post('/user_management/bulk/', {'action': 'delete', 'confirm': am.DELETE_CONFIRMATION, 'ids': [student.pk]})
    assert not User.objects.filter(username=username).exists()
    assert not os.path.exists(home)
    assert not os.path.exists(review_dir)
    assert not AccessAttempt.objects.filter(username=username).exists()
    assert AuditLog.objects.filter(username=username, action='LOGIN').exists()
    # the student's session is gone
    assert student_client.get('/overview/').status_code == 302


def test_deleting_group_admin_cascades(admin, teacher):
    usernames = [u for u, _ in create(teacher, ['a', 'b'], prefix='kurs').created]
    deleted = am.delete_accounts([teacher], actor=admin)
    assert set(deleted) == {'mueller', *usernames}
    assert not User.objects.filter(username__in=usernames).exists()
    for u in usernames:
        assert not os.path.exists(get_user_home_directory(u))
    assert not AccountPrefix.objects.filter(name='kurs').exists()


def test_delete_refuses_admin_and_self(admin, teacher):
    with pytest.raises(am.AccountManagementError):
        am.delete_accounts([teacher], actor=teacher)
    with pytest.raises(am.AccountManagementError):
        am.delete_accounts([admin], actor=teacher)
    assert User.objects.filter(pk=teacher.pk).exists()


# --------------------------------------------------------------------------------------
# Locking and schedules
# --------------------------------------------------------------------------------------

def test_apply_schedules(teacher):
    a, b, c = [User.objects.get(username=u) for u, _ in create(teacher, ['a', 'b', 'c']).created]
    past = timezone.now() - timedelta(minutes=1)
    AccountProfile.objects.filter(user=a).update(lock_at=past)
    AccountProfile.objects.filter(user=b).update(delete_at=past)
    result = am.apply_schedules()
    assert result['locked'] == 1
    assert result['deleted'] == 1
    a.refresh_from_db()
    assert not a.is_active
    assert a.profile.lock_at is None
    assert not User.objects.filter(pk=b.pk).exists()
    c.refresh_from_db()
    assert c.is_active


def test_locked_user_cannot_log_in(teacher):
    username, password = create(teacher, ['a']).created[0]
    am.lock_accounts(User.objects.filter(username=username))
    response = Client().post('/accounts/login/', {'username': username, 'password': password})
    assert response.status_code == 200
    assert 'gesperrt' in response.content.decode()
    assert not response.wsgi_request.user.is_authenticated


def test_scheduled_lock_ends_running_session(teacher):
    username = create(teacher, ['a']).created[0][0]
    student = User.objects.get(username=username)
    c = client_for(student)
    assert c.get('/overview/').status_code == 200
    AccountProfile.objects.filter(user=student).update(lock_at=timezone.now() - timedelta(seconds=1))
    assert c.get('/overview/').status_code == 302
    student.refresh_from_db()
    assert not student.is_active


def test_bulk_set_and_clear_dates(teacher):
    a = User.objects.get(username=create(teacher, ['a']).created[0][0])
    future = (timezone.localtime() + timedelta(days=30)).strftime('%Y-%m-%dT%H:%M')
    c = client_for(teacher)
    c.post('/user_management/bulk/', {'action': 'set_dates', 'ids': [a.pk], 'bulk_delete_at': future})
    assert get_profile(a).delete_at is not None
    c.post('/user_management/bulk/', {'action': 'set_dates', 'ids': [a.pk], 'clear_delete_at': '1'})
    assert get_profile(a).delete_at is None


def test_reset_password(teacher):
    username, old = create(teacher, ['a']).created[0]
    user = User.objects.get(username=username)
    client_for(teacher).post('/user_management/bulk/', {'action': 'reset_password', 'ids': [user.pk]})
    user.refresh_from_db()
    assert not user.check_password(old)


# --------------------------------------------------------------------------------------
# Review slot
# --------------------------------------------------------------------------------------

def test_review_slot(teacher):
    username = create(teacher, ['gruppe1'], prefix='kurs').created[0][0]
    student = User.objects.get(username=username)
    home = get_user_home_directory(username)
    with open(os.path.join(home, 'kundenliste.sql'), 'w') as f:
        f.write('SELECT * FROM kunde;')

    c = client_for(teacher)
    # 'mueller' has no own workspace: no access before reviewing
    assert c.get('/overview/').status_code == 302

    response = c.post(f'/user_management/review/{student.pk}/')
    assert response.status_code == 302
    assert response['Location'].endswith('/overview/')
    review_dir = get_review_directory(teacher.pk)
    assert os.path.isfile(os.path.join(review_dir, 'kundenliste.sql'))
    with open(os.path.join(review_dir, REVIEW_SOURCE_MARKER)) as f:
        assert f.read() == str(student.pk)

    page = c.get('/overview/')
    assert page.status_code == 200
    content = page.content.decode()
    assert 'kundenliste' in content
    assert 'review-banner' in content

    # Changes in the review copy never reach the original
    with open(os.path.join(review_dir, 'neu.sql'), 'w') as f:
        f.write('SELECT 2;')
    assert not os.path.exists(os.path.join(home, 'neu.sql'))

    c.post('/user_management/review/exit/')
    assert c.get('/overview/').status_code == 302


def test_review_does_not_touch_own_project():
    reviewer = make_group_admin('lehrer_admin')
    own_home = get_user_home_directory(reviewer.username)
    os.makedirs(own_home)
    with open(os.path.join(own_home, 'meins.sql'), 'w') as f:
        f.write('SELECT 1;')
    student = User.objects.get(username=create(reviewer, ['g'], prefix='k').created[0][0])

    am.start_review(reviewer, student)
    assert os.path.isfile(os.path.join(own_home, 'meins.sql'))
    assert get_user_directory(reviewer.username) == own_home  # outside a review request


# --------------------------------------------------------------------------------------
# Export
# --------------------------------------------------------------------------------------

def test_export_zip(teacher):
    usernames = [u for u, _ in create(teacher, ['a', 'b'], prefix='kurs').created]
    with open(os.path.join(get_user_home_directory(usernames[0]), 'datenbank.db'), 'wb') as f:
        f.write(b'SQLite')
    response = client_for(teacher).post('/user_management/bulk/', {
        'action': 'download', 'ids': list(User.objects.filter(username__in=usernames).values_list('pk', flat=True)),
    })
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/zip'
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        names = z.namelist()
        assert 'kurs-a/datenbank.db' in names
        assert 'accounts.csv' in names
        csv_text = z.read('accounts.csv').decode('utf-8-sig')
        assert 'kurs-a_admin' in csv_text
        assert 'kurs-b_admin' in csv_text
