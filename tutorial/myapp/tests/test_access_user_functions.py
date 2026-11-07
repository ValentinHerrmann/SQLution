"""Tests for the placeholders {name} / {name}[SQL] of the Nutzerfunktionen and their execution.

Like test_access_management.py, this module is named so it is collected before test_coverage.py
(which replaces several myapp modules in sys.modules with stubs)."""
import os
import sqlite3

import pytest
from django.contrib.auth.models import User

import myapp.views.user_functions  # noqa: F401  (imported early, see test_access_management.py)
from myapp.utils.directories import get_user_home_directory
from myapp.utils.placeholders import (
    find_dropdowns,
    find_inputs,
    strip_dropdown_sql,
    substitute_placeholders,
)

from test_account_management import (  # noqa: F401  (fixtures are used by name)
    admin,
    client_for,
    create,
    isolated,
    make_group_admin,
    teacher,
    test_database,
)

pytestmark = pytest.mark.no_auth_bypass


# --------------------------------------------------------------------------------------
# Finding and stripping
# --------------------------------------------------------------------------------------

def test_adjacent_inputs_are_both_found():
    assert find_inputs('SELECT {a}{b}') == ['a', 'b']


def test_inputs_are_deduplicated_and_dropdowns_excluded():
    sql = "SELECT {a}, {a}, {b} FROM t WHERE x={b}[SELECT 1] AND y={c}"
    assert find_inputs(sql) == ['a', 'c']
    assert find_dropdowns(sql) == [('b', 'SELECT 1')]


def test_glob_and_column_brackets_are_preserved():
    sql = "SELECT [col] FROM t WHERE n GLOB '[a-z]*' AND k={x}[SELECT id FROM t]"
    assert find_inputs(sql) == []
    assert strip_dropdown_sql(sql) == "SELECT [col] FROM t WHERE n GLOB '[a-z]*' AND k={x}"


# --------------------------------------------------------------------------------------
# Substituting
# --------------------------------------------------------------------------------------

def test_dropdown_values_are_inserted_unchanged_outside_quotes():
    for value in ['(1)', 'a,b', "it's", '']:
        assert substitute_placeholders('SELECT {x}', {'x': value}) == 'SELECT ' + value


def test_value_containing_placeholder_is_not_substituted_again():
    assert substitute_placeholders('SELECT {a}, {b}', {'a': '{b}', 'b': '2'}) == 'SELECT {b}, 2'


def test_unknown_placeholder_stays():
    assert substitute_placeholders('SELECT {a}, {z}', {'a': '1'}) == 'SELECT 1, {z}'


def test_quotes_are_doubled_inside_literals():
    assert substitute_placeholders("WHERE n='{n}'", {'n': "O'Brien"}) == "WHERE n='O''Brien'"
    assert substitute_placeholders('WHERE n="{n}"', {'n': 'a"b'}) == 'WHERE n="a""b"'
    # the other quote character is not touched
    assert substitute_placeholders('WHERE n="{n}"', {'n': "O'Brien"}) == 'WHERE n="O\'Brien"'
    # a closed literal before the placeholder does not count
    assert substitute_placeholders("WHERE a='x' AND n={n}", {'n': "O'B"}) == "WHERE a='x' AND n=O'B"
    assert substitute_placeholders("WHERE a='it''s' AND n='{n}'", {'n': "O'B"}) == "WHERE a='it''s' AND n='O''B'"


def test_string_key_works_end_to_end_in_sqlite():
    """Issue #35: a text primary key chosen from a dropdown, the placeholder in quotes."""
    sql = strip_dropdown_sql("SELECT * FROM t WHERE id='{x}[SELECT id FROM t]'")
    con = sqlite3.connect(':memory:')
    con.execute("CREATE TABLE t (id TEXT PRIMARY KEY, n TEXT)")
    con.execute("INSERT INTO t VALUES ('O''Brien', 'x'), ('abc', 'y')")
    for key, expected in [("O'Brien", 'x'), ('abc', 'y')]:
        query = substitute_placeholders(sql, {'x': key})
        assert con.execute(query).fetchall() == [(key, expected)]


# --------------------------------------------------------------------------------------
# The view
# --------------------------------------------------------------------------------------

@pytest.fixture
def project(teacher):
    """db-admin 'gruppe1_admin' with a DB containing a table with a text primary key (NULL, comma, apostrophe)."""
    create(teacher, ['gruppe1'])
    student = User.objects.get(username='gruppe1_admin')
    directory = get_user_home_directory(student.username)
    os.makedirs(directory, exist_ok=True)
    con = sqlite3.connect(os.path.join(directory, 'datenbank.db'))
    con.execute("CREATE TABLE t (id TEXT PRIMARY KEY, name TEXT)")
    con.executemany("INSERT INTO t VALUES (?, ?)", [("O'Brien", 'Irish'), ('a,b', 'Comma'), ('(x)', None)])
    con.commit()
    con.close()
    return student, directory


def write_query(directory, name, sql):
    with open(os.path.join(directory, name + '.sql'), 'w', encoding='utf-8') as f:
        f.write(sql)


def test_execute_with_dropdown_and_text_key(project):
    student, directory = project
    write_query(directory, 'Suche', "SELECT name FROM t WHERE id='{Schluessel}[SELECT id, name FROM t ORDER BY id]'")
    c = client_for(student)

    response = c.get('/user_functions/execute/?file=Suche')
    assert response.status_code == 200
    content = response.content.decode()
    assert 'value="O&#x27;Brien"' in content
    assert 'O&#x27;Brien, Irish' in content  # label shows all columns
    assert 'value="a,b"' in content
    assert '(x), ' in content  # NULL becomes an empty string in the label

    for key, name in [("O'Brien", 'Irish'), ('a,b', 'Comma'), ('(x)', None)]:
        response = c.post('/user_functions/execute/?file=Suche', {'dropdown_Schluessel': key})
        content = response.content.decode()
        assert 'Fehler' not in content
        if name:
            assert f'>{name}</td>' in content


def test_execute_with_inputs_and_escaped_query_display(project):
    student, directory = project
    write_query(directory, 'Zwei', "SELECT '{a}' AS a, '{b}' AS b\nFROM t WHERE '<' = '<'")
    c = client_for(student)
    response = c.post('/user_functions/execute/?file=Zwei', {'input_a': "O'B", 'input_b': '<b>x</b>'})
    content = response.content.decode()
    assert 'Fehler' not in content
    assert '>O&#x27;B</td>' in content
    assert '&lt;b&gt;x&lt;/b&gt;' in content  # the admin view shows the query escaped
    assert '<b>x</b>' not in content
    assert '<br>FROM t' in content
