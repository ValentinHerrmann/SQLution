"""Tests for db-users managed by their db-admin (issue #74) and query visibility (issue #76).

Like test_account_management.py, this module is named so it is collected before
test_coverage.py (which replaces several myapp modules in sys.modules with stubs).
It reuses the fixtures and helpers of test_account_management.py.
"""
import io
import json
import os
import zipfile
from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

import myapp.views.db_users  # noqa: F401  (imported early, see module docstring)
import myapp.views.files  # noqa: F401
import myapp.views.user_functions  # noqa: F401
from myapp.models import get_profile
from myapp.utils import account_management as am
from myapp.utils import db_users as du
from myapp.utils import query_access as qa
from myapp.utils.directories import get_user_home_directory
from myapp.utils.roles import can_manage_db_users, managed_queryset

from test_account_management import (  # noqa: F401  (fixtures are used by name)
    admin,
    client_for,
    create,
    isolated,
    make_group_admin,
    message_texts,
    teacher,
    test_database,
)

pytestmark = pytest.mark.no_auth_bypass


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------

@pytest.fixture
def student(teacher):
    """A db-admin account created by the teacher: 'gruppe1_admin', folder 'gruppe1'."""
    create(teacher, ['gruppe1'])
    return User.objects.get(username='gruppe1_admin')


def project_dir(admin):
    directory = get_user_home_directory(admin.username)
    os.makedirs(directory, exist_ok=True)
    return directory


def write_query(directory, name, sql='SELECT 1'):
    with open(os.path.join(directory, name + '.sql'), 'w', encoding='utf-8') as f:
        f.write(sql)


def read_file(directory, filename):
    with open(os.path.join(directory, filename), 'r', encoding='utf-8') as f:
        return f.read()


def create_db_users(admin, names, **kwargs):
    result = du.create_db_users(admin, names, **kwargs)
    assert result.ok, result.errors
    return result


# --------------------------------------------------------------------------------------
# query_access: the access file
# --------------------------------------------------------------------------------------

def test_new_queries_are_hidden(tmp_path):
    directory = str(tmp_path / 'p')
    os.makedirs(directory)
    qa.save_access(directory, {})
    write_query(directory, 'Neu')
    assert qa.visible_queries(directory, 'leser') == []


def test_can_see_all_and_single_users(tmp_path):
    directory = str(tmp_path / 'p')
    os.makedirs(directory)
    for name in ('Preise', 'Bestellungen', 'Intern'):
        write_query(directory, name)
    qa.save_access(directory, {'Preise': qa.ALL, 'Bestellungen': ['kasse']})
    assert qa.visible_queries(directory, 'kasse') == ['Bestellungen', 'Preise']
    assert qa.visible_queries(directory, 'leser') == ['Preise']


def test_save_drops_unknown_queries_and_bad_values(tmp_path):
    directory = str(tmp_path / 'p')
    os.makedirs(directory)
    write_query(directory, 'A')
    saved = qa.save_access(directory, {'A': ['x', 'x', 3], 'Weg': qa.ALL, 'B': 'quatsch'})
    assert saved == {'A': ['x']}


def test_broken_access_file_hides_everything_and_is_not_converted(tmp_path):
    directory = str(tmp_path / 'p')
    os.makedirs(directory)
    write_query(directory, 'leser_X')
    with open(os.path.join(directory, qa.ACCESS_FILE), 'w') as f:
        f.write('{kaputt')
    assert qa.load_access(directory) == {}
    assert os.path.exists(os.path.join(directory, 'leser_X.sql'))  # not renamed


def test_rename_and_remove_keep_the_file_in_sync(tmp_path):
    directory = str(tmp_path / 'p')
    os.makedirs(directory)
    write_query(directory, 'Alt')
    write_query(directory, 'Andere')
    qa.save_access(directory, {'Alt': ['leser'], 'Andere': qa.ALL})

    qa.rename_query(directory, 'Alt.sql', 'Neu.sql')
    assert qa.load_access(directory) == {'Neu': ['leser'], 'Andere': qa.ALL}
    with pytest.raises(FileExistsError):
        qa.rename_query(directory, 'Neu', 'Andere')
    with pytest.raises(FileNotFoundError):
        qa.rename_query(directory, 'Gibtsnicht', 'X')

    os.remove(os.path.join(directory, 'Andere.sql'))
    qa.remove_query(directory, 'Andere.sql')
    assert qa.load_access(directory) == {'Neu': ['leser']}


# --------------------------------------------------------------------------------------
# query_access: converting the old file-name convention
# --------------------------------------------------------------------------------------

def test_legacy_conversion(tmp_path):
    directory = str(tmp_path / 'p')
    os.makedirs(directory)
    write_query(directory, 'Preise')
    write_query(directory, 'leser_Bestellungen', 'SELECT * FROM bestellung')
    write_query(directory, 'Gesamt', 'SELECT * FROM (<<leser_Bestellungen>>) JOIN (<<leser_Bestellungen.sql>>)')

    access = qa.load_access(directory)

    assert access == {'Preise': qa.ALL, 'Gesamt': qa.ALL, 'Bestellungen': ['leser']}
    assert qa.list_queries(directory) == ['Bestellungen', 'Gesamt', 'Preise']
    # renamed file: backup under its old name
    assert read_file(directory, 'leser_Bestellungen.sql_bak') == 'SELECT * FROM bestellung'
    # subquery references are rewritten, the original is backed up
    assert read_file(directory, 'Gesamt.sql') == 'SELECT * FROM (<<Bestellungen>>) JOIN (<<Bestellungen>>)'
    assert '<<leser_Bestellungen>>' in read_file(directory, 'Gesamt.sql_bak')
    assert not os.path.exists(os.path.join(directory, 'Preise.sql_bak'))  # untouched files: no backup


def test_legacy_conversion_keeps_name_on_collision(tmp_path):
    directory = str(tmp_path / 'p')
    os.makedirs(directory)
    write_query(directory, 'a_Liste')
    write_query(directory, 'b_Liste')
    write_query(directory, 'c_Preise')
    write_query(directory, 'Preise')

    access = qa.load_access(directory)

    assert access == {'Liste': ['a'], 'b_Liste': ['b'], 'c_Preise': ['c'], 'Preise': qa.ALL}
    assert qa.list_queries(directory) == ['Liste', 'Preise', 'b_Liste', 'c_Preise']


def test_legacy_conversion_runs_once(tmp_path):
    directory = str(tmp_path / 'p')
    os.makedirs(directory)
    write_query(directory, 'leser_X')
    qa.load_access(directory)
    write_query(directory, 'kasse_Y')  # created after the conversion: a normal name now
    assert qa.load_access(directory) == {'X': ['leser']}
    assert qa.list_queries(directory) == ['X', 'kasse_Y']


# --------------------------------------------------------------------------------------
# Creating db-users
# --------------------------------------------------------------------------------------

def test_create_db_users(student, teacher):
    result = create_db_users(student, ['Kasse', 'Leser'])
    assert [u for u, _ in result.created] == ['gruppe1_kasse', 'gruppe1_leser']
    assert sorted(du.short_name(u) for u in du.db_users_of(student)) == ['kasse', 'leser']
    # the teacher still manages them
    assert set(managed_queryset(teacher).values_list('username', flat=True)) == {
        'gruppe1_admin', 'gruppe1_kasse', 'gruppe1_leser'}


def test_db_users_inherit_course_and_dates(teacher):
    lock_at = timezone.now() + timedelta(days=3)
    create(teacher, ['team'], prefix='q11inf', lock_at=lock_at)
    admin = User.objects.get(username='q11inf-team_admin')
    create_db_users(admin, ['leser'])
    profile = get_profile(User.objects.get(username='q11inf-team_leser'))
    assert profile.managed_by == teacher
    assert profile.prefix.name == 'q11inf'
    assert profile.lock_at == lock_at


def test_create_db_users_validates_everything_first(student):
    create_db_users(student, ['leser'])
    result = du.create_db_users(student, ['kasse', 'leser', 'admin', '!!!', 'kasse'])
    joined = ' '.join(result.errors)
    assert '„leser“ gibt es schon.' in joined
    assert '„admin“ ist reserviert.' in joined
    assert 'kein gültiger Name' in joined
    assert '„kasse“ kommt mehrfach vor.' in joined
    assert not User.objects.filter(username='gruppe1_kasse').exists()


def test_underscore_in_db_user_name_is_replaced(student):
    """'_' only separates the data folder, so it never ends up in a name (issue #89)."""
    result = create_db_users(student, ['kas_se'])
    assert [u for u, _ in result.created] == ['gruppe1_kas-se']
    assert get_user_home_directory('gruppe1_kas-se') == get_user_home_directory(student.username)


def test_create_db_users_limit(student, monkeypatch):
    monkeypatch.setattr(du, 'MAX_DB_USERS_PER_PROJECT', 2)
    create_db_users(student, ['a'])
    result = du.create_db_users(student, ['b', 'c'])
    assert any('Höchstens 2' in e for e in result.errors)


def test_who_may_manage_db_users(student, teacher):
    create_db_users(student, ['leser'])
    leser = User.objects.get(username='gruppe1_leser')
    legacy = User.objects.create_user(username='max_mueller_admin', password='x')  # issue #89
    assert can_manage_db_users(student)
    assert not can_manage_db_users(teacher)
    assert not can_manage_db_users(leser)
    assert not can_manage_db_users(legacy)
    assert not du.create_db_users(leser, ['x']).ok

    student.in_review = True
    assert not can_manage_db_users(student)


def test_db_admin_cannot_touch_foreign_users(student, teacher):
    create(teacher, ['gruppe2'])
    other = User.objects.get(username='gruppe2_admin')
    create_db_users(other, ['leser'])
    foreign = User.objects.get(username='gruppe2_leser')

    c = client_for(student)
    c.post('/db_users/bulk/', {'action': 'delete', 'ids': [foreign.pk, other.pk], 'confirm': am.DELETE_CONFIRMATION})
    assert User.objects.filter(pk__in=[foreign.pk, other.pk]).count() == 2


# --------------------------------------------------------------------------------------
# Deleting
# --------------------------------------------------------------------------------------

def test_deleting_db_user_keeps_project_and_db_admin(student):
    directory = project_dir(student)
    write_query(directory, 'X')
    create_db_users(student, ['leser', 'kasse'])
    leser = User.objects.get(username='gruppe1_leser')

    deleted = am.delete_accounts([leser], actor=student)

    assert deleted == ['gruppe1_leser']
    assert os.path.exists(os.path.join(directory, 'X.sql'))
    assert User.objects.filter(username__in=['gruppe1_admin', 'gruppe1_kasse']).count() == 2


def test_deleting_db_admin_still_deletes_its_db_users(student, teacher):
    project_dir(student)
    create_db_users(student, ['leser'])
    deleted = am.delete_accounts([student], actor=teacher)
    assert sorted(deleted) == ['gruppe1_admin', 'gruppe1_leser']
    assert not os.path.exists(get_user_home_directory('gruppe1_admin'))


def test_deleting_old_plain_user_account_keeps_project(admin):
    """Before the Accountverwaltung, a project could have a plain user account 'firma' that sees all queries."""
    firma_admin = User.objects.create_user(username='firma_admin', password='x')
    firma = User.objects.create_user(username='firma', password='x')
    kasse = User.objects.create_user(username='firma_kasse', password='x')
    directory = project_dir(firma_admin)
    write_query(directory, 'X')

    deleted = am.delete_accounts([firma], actor=admin)

    assert deleted == ['firma']
    assert os.path.exists(os.path.join(directory, 'X.sql'))
    assert User.objects.filter(pk__in=[firma_admin.pk, kasse.pk]).count() == 2
    # without a '<base>_admin' a plain account still owns its folder (e.g. a group admin)
    assert am.owns_data_folder(User.objects.create_user(username='mueller2', password='x'))


def test_bulk_delete_needs_confirmation(student):
    create_db_users(student, ['leser'])
    leser = User.objects.get(username='gruppe1_leser')
    c = client_for(student)
    c.post('/db_users/bulk/', {'action': 'delete', 'ids': [leser.pk], 'confirm': 'nein'})
    assert User.objects.filter(pk=leser.pk).exists()
    c.post('/db_users/bulk/', {'action': 'delete', 'ids': [leser.pk], 'confirm': am.DELETE_CONFIRMATION})
    assert not User.objects.filter(pk=leser.pk).exists()


# --------------------------------------------------------------------------------------
# Views
# --------------------------------------------------------------------------------------

def test_page_access(student, teacher):
    assert client_for(student).get('/db_users/').status_code == 200
    assert client_for(teacher).get('/db_users/').status_code == 302
    create_db_users(student, ['leser'])
    assert client_for(User.objects.get(username='gruppe1_leser')).get('/db_users/').status_code == 302


def test_create_view_shows_passwords_once(student):
    c = client_for(student)
    response = c.post('/db_users/create/', {'names': 'leser\nkasse', 'shared_password': ''}, follow=True)
    content = response.content.decode()
    assert 'gruppe1_leser' in content
    assert 'Zugangsdaten' in content
    assert 'Zugangsdaten' not in c.get('/db_users/').content.decode()


def test_save_access_matrix(student):
    directory = project_dir(student)
    for name in ('Preise', 'Bestellungen', 'Intern'):
        write_query(directory, name)
    create_db_users(student, ['leser', 'kasse'])

    c = client_for(student)
    c.post('/db_users/access/', {'access': [
        '*:Preise', 'leser:Preise',             # "Alle" wins
        'kasse:Bestellungen',
        'fremd:Intern', 'leser:Gibtsnicht',      # unknown user / query: ignored
    ]})

    with open(os.path.join(directory, qa.ACCESS_FILE), encoding='utf-8') as f:
        assert json.load(f) == {'Preise': qa.ALL, 'Bestellungen': ['kasse']}


def test_split_category():
    assert qa.split_category('Kunden - Liste') == ('Kunden', 'Liste')
    assert qa.split_category('Kunden - Liste - alt') == ('Kunden', 'Liste - alt')
    assert qa.split_category('Liste') == (qa.DEFAULT_CATEGORY, 'Liste')


def test_category_prefix_hidden_on_buttons_and_matrix(student):
    """The category is already the heading, the button and the matrix row only show the rest (issue #161)."""
    directory = project_dir(student)
    write_query(directory, 'Kunden - Liste')
    create_db_users(student, ['leser'])
    c = client_for(student)

    content = c.get('/user_functions/').content.decode()
    assert '<h4>Kunden</h4>' in content
    assert '>Liste</a>' in content
    assert '?file=Kunden - Liste"' in content

    content = c.get('/db_users/').content.decode()
    assert '<td>Liste</td>' in content
    assert 'value="leser:Kunden - Liste"' in content


def test_user_functions_respect_access(student):
    directory = project_dir(student)
    write_query(directory, 'Preise', 'SELECT 1 AS preis')
    write_query(directory, 'Geheim', 'SELECT 2')
    qa.save_access(directory, {'Preise': qa.ALL})
    create_db_users(student, ['leser'])
    c = client_for(User.objects.get(username='gruppe1_leser'))

    content = c.get('/user_functions/').content.decode()
    assert 'Preise' in content
    assert 'Geheim' not in content
    assert c.get('/user_functions/execute/?file=Preise').status_code == 200

    response = c.get('/user_functions/execute/?file=Geheim')
    assert response.status_code == 302  # logged out
    assert '/accounts/login/' in response.url

    admin_content = client_for(student).get('/user_functions/').content.decode()
    assert 'Preise' in admin_content
    assert 'Geheim' in admin_content


def test_upload_of_old_project_zip_gets_converted(student):
    directory = project_dir(student)
    write_query(directory, 'Neu')
    qa.save_access(directory, {'Neu': qa.ALL})

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zipf:
        zipf.writestr('leser_Alt.sql', 'SELECT 1')
    buffer.seek(0)
    buffer.name = 'projekt.zip'
    client_for(student).post('/upload_zip/', {'zip_file': buffer})

    assert qa.load_access(directory) == {'Neu': qa.ALL, 'Alt': ['leser']}


def test_rename_api_moves_access(student):
    directory = project_dir(student)
    write_query(directory, 'Alt')
    qa.save_access(directory, {'Alt': ['leser']})
    c = client_for(student)
    response = c.post('/api/sql/rename', json.dumps({'old': 'Alt.sql', 'new': 'Neu.sql'}), content_type='application/json')
    assert response.status_code == 200
    assert qa.load_access(directory) == {'Neu': ['leser']}
    response = c.post('/api/sql/rename', json.dumps({'old': 'Gibtsnicht', 'new': 'X'}), content_type='application/json')
    assert response.status_code == 404


def test_account_table_lists_db_users_below_their_db_admin(student, teacher):
    create(teacher, ['aaa'])
    create_db_users(student, ['abc'])
    content = client_for(teacher).get('/user_management/').content.decode()
    order = [content.index(name) for name in ('aaa_admin', 'gruppe1_admin', 'gruppe1_abc')]
    assert order == sorted(order)


# --------------------------------------------------------------------------------------
# Review: only by the account's own group admin
# --------------------------------------------------------------------------------------

def test_only_own_group_admin_may_review(admin, student, teacher):
    create_db_users(student, ['leser'])
    leser = User.objects.get(username='gruppe1_leser')
    independent = User.objects.get(username=am.create_accounts(admin, ['solo']).created[0][0])
    other_teacher = make_group_admin('schmidt')

    for actor, target in [(admin, student), (admin, independent), (other_teacher, student),
                          (other_teacher, leser), (teacher, independent)]:
        assert client_for(actor).post(f'/user_management/review/{target.pk}/').status_code == 404, (actor, target)

    # the Review button is only shown where it works
    content = client_for(admin).get('/user_management/').content.decode()
    assert 'data-review-url="' not in content
    content = client_for(teacher).get('/user_management/').content.decode()
    assert content.count('data-review-url="') == 2  # gruppe1_admin and gruppe1_leser


def test_reviewing_db_user_shows_its_view(student, teacher):
    directory = project_dir(student)
    write_query(directory, 'Preise')
    write_query(directory, 'Geheim')
    qa.save_access(directory, {'Preise': ['leser']})
    create_db_users(student, ['leser'])
    leser = User.objects.get(username='gruppe1_leser')

    c = client_for(teacher)
    response = c.post(f'/user_management/review/{leser.pk}/')
    assert response.status_code == 302
    assert response['Location'].endswith('/user_functions/')

    content = c.get('/user_functions/').content.decode()
    assert 'Preise' in content
    assert 'Geheim' not in content
    assert 'Nutzersicht von' in content
    assert c.get('/overview/').status_code == 302  # no db-admin rights in a db-user's view
    assert c.get('/user_functions/execute/?file=Preise').status_code == 200

    # reviewing the db-admin afterwards: full project again
    response = c.post(f'/user_management/review/{student.pk}/')
    assert response['Location'].endswith('/overview/')
    content = c.get('/user_functions/').content.decode()
    assert 'Preise' in content
    assert 'Geheim' in content
