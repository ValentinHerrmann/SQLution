"""Tests for changing the own password (issue #165).

Named so it is collected before test_coverage.py, which replaces several myapp
modules in sys.modules with stubs at import time. Everything is imported here.
"""
import os

import pytest
from django.contrib.auth.models import Group, User
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.db import transaction
from django.test import Client

import myapp.context_processors  # noqa: F401  (imported early, see module docstring)
import myapp.middleware  # noqa: F401
import myapp.urls  # noqa: F401
from myapp.utils import account_management as am
from myapp.utils.roles import GROUP_ADMIN_GROUP, can_change_own_password

pytestmark = pytest.mark.no_auth_bypass

URL = '/accounts/password/'
OLD = 'Alt-Passwort-123x'
NEW = 'Neu-Passwort-456y'


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


def make_user(username, group_admin=False):
    user = User.objects.create_user(username=username, password=OLD)
    if group_admin:
        user.groups.add(Group.objects.get_or_create(name=GROUP_ADMIN_GROUP)[0])
    return User.objects.get(pk=user.pk)


def client_for(user):
    c = Client()
    c.force_login(user)
    return c


def passwords(old=OLD, new=NEW, confirm=NEW):
    return {'old_password': old, 'new_password1': new, 'new_password2': confirm}


def password_ok(username, password):
    return User.objects.get(username=username).check_password(password)


@pytest.mark.parametrize('username, group_admin, page', [
    ('admin', False, '/user_management/'),
    ('mueller', True, '/user_management/'),
    ('kurs_admin', False, '/db_users/'),
])
def test_allowed_roles_change_password(username, group_admin, page):
    user = make_user(username, group_admin)
    c = client_for(user)
    response = c.post(URL, passwords())
    assert response.status_code == 302
    assert response['Location'] == page
    assert password_ok(username, NEW)
    assert not password_ok(username, OLD)
    assert c.get(page).status_code == 200  # current session stays logged in


def test_other_sessions_are_ended():
    user = make_user('mueller', True)
    current, other = client_for(user), client_for(user)
    assert other.get('/user_management/').status_code == 200
    assert current.post(URL, passwords()).status_code == 302
    assert current.get('/user_management/').status_code == 200
    assert other.get('/user_management/').status_code == 302


@pytest.mark.parametrize('username', ['kurs_schueler', 'kurs'])
def test_db_users_and_old_accounts_are_refused(username):
    make_user(username)
    c = client_for(User.objects.get(username=username))
    assert c.post(URL, passwords()).status_code in (302, 403)
    assert password_ok(username, OLD)
    assert not password_ok(username, NEW)


def test_group_admin_in_review_is_refused():
    teacher = make_user('mueller', True)
    student = am.create_accounts(teacher, ['gruppe1'], prefix='kurs').created[0][0]
    student = User.objects.get(username=student)
    c = client_for(teacher)
    assert c.post(f'/user_management/review/{student.pk}/').status_code == 302
    assert c.post(URL, passwords()).status_code in (302, 403)
    assert password_ok('mueller', OLD)
    assert not password_ok('mueller', NEW)
    assert 'Eigenes Passwort ändern' not in c.get('/overview/').content.decode()


def test_can_change_own_password_roles():
    assert can_change_own_password(make_user('admin'))
    assert can_change_own_password(make_user('mueller', True))
    assert can_change_own_password(make_user('kurs_admin'))
    assert not can_change_own_password(make_user('kurs_schueler'))
    assert not can_change_own_password(make_user('kurs'))


@pytest.mark.parametrize('data', [
    passwords(old='falsch'),
    passwords(confirm='Anders-789z'),
])
def test_invalid_input_keeps_password(data):
    make_user('admin')
    c = client_for(User.objects.get(username='admin'))
    assert c.post(URL, data).status_code == 302
    assert password_ok('admin', OLD)


def test_get_not_allowed():
    make_user('admin')
    assert client_for(User.objects.get(username='admin')).get(URL).status_code == 405


@pytest.mark.parametrize('username, group_admin, page', [
    ('mueller', True, '/user_management/'),
    ('kurs_admin', False, '/db_users/'),
])
def test_card_on_both_pages(username, group_admin, page):
    c = client_for(make_user(username, group_admin))
    content = c.get(page).content.decode()
    assert 'Eigenes Passwort ändern' in content
    assert 'name="new_password2"' in content


def test_end_sessions_without_keep_ends_all():
    user = make_user('mueller', True)
    client_for(user)
    client_for(user)
    assert Session.objects.count() == 2
    assert am.end_sessions([user], 'Test') == 2
    assert Session.objects.count() == 0
