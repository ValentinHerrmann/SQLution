"""
Tests for the PDF export of query results (Nutzerfunktionen).
"""

import os
import sqlite3
import sys
from unittest.mock import MagicMock, patch

import pytest
from django.test import RequestFactory

tests_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(tests_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from myapp.utils.pdf_export import build_result_pdf, pdf_filename
from myapp.views import user_functions


class TestBuildResultPdf:

    def test_returns_pdf_bytes(self):
        pdf = build_result_pdf('Schüler', ['id', 'name'], [(1, 'Anna'), (2, 'Ben')])
        assert pdf.startswith(b'%PDF')

    def test_handles_special_characters_and_empty_cells(self):
        pdf = build_result_pdf('<A & B>', ['a<b', 'c&d'], [(None, ''), ('x < y & z', 'line1\nline2')])
        assert pdf.startswith(b'%PDF')

    def test_handles_many_columns_and_rows(self):
        columns = [f'col{i}' for i in range(20)]
        rows = [tuple(f'value {r}-{c}' for c in range(20)) for r in range(200)]
        assert build_result_pdf('Viele Daten', columns, rows).startswith(b'%PDF')

    def test_handles_no_rows(self):
        assert build_result_pdf('Leer', ['id'], []).startswith(b'%PDF')

    def test_uses_a4_page_size(self):
        pdf = build_result_pdf('A4', ['id'], [(1,)])
        assert b'/MediaBox [ 0 0 595.2756 841.8898 ]' in pdf

    def test_filename_is_ascii_safe(self):
        name = pdf_filename('Schüler / Klasse "5a"')
        assert name.endswith('.pdf')
        assert name.isascii()
        assert '/' not in name and '"' not in name


class TestUserFunctionsExportView:

    @pytest.fixture
    def setup(self, tmp_path):
        user_dir = tmp_path / 'user'
        user_dir.mkdir()
        (user_dir / 'Alle Schüler.sql').write_text('SELECT * FROM t')
        (user_dir / 'Suche.sql').write_text("SELECT * FROM t WHERE name = '{Name}' ")

        con = sqlite3.connect(':memory:')
        con.execute('CREATE TABLE t (id INTEGER, name TEXT)')
        con.execute("INSERT INTO t VALUES (1, 'Anna'), (2, 'Ben')")

        def fake_run_sql(sql, username):
            cur = con.cursor()
            for stmt in sql.split(';'):
                if stmt.strip():
                    cur.execute(stmt)
            return cur

        user = MagicMock(username='test', is_authenticated=True)
        # Patch every helper explicitly: other test modules replace myapp.utils.* with stubs in sys.modules
        with patch.object(user_functions, 'get_user_directory', return_value=str(user_dir) + '/', create=True), \
             patch.object(user_functions, 'get_user_suffix', return_value='', create=True), \
             patch.object(user_functions, 'fullpath', side_effect=os.path.join, create=True), \
             patch.object(user_functions, 'remove_nones_from_sqlresult', side_effect=lambda r: list(r), create=True), \
             patch.object(user_functions, 'runSql', side_effect=fake_run_sql, create=True), \
             patch.object(user_functions, 'resolve_subqueries', side_effect=lambda sql, username: sql, create=True):
            yield RequestFactory(), user

    def test_get_export_without_inputs_returns_pdf(self, setup):
        factory, user = setup
        request = factory.get('/user_functions/execute/', {'file': 'Alle Schüler', 'export': 'pdf'})
        request.user = user
        response = user_functions.user_functions_execute(request)
        assert response['Content-Type'] == 'application/pdf'
        assert 'attachment' in response['Content-Disposition']
        assert response.content.startswith(b'%PDF')

    def test_post_export_with_inputs_returns_pdf(self, setup):
        factory, user = setup
        request = factory.post('/user_functions/execute/?file=Suche', {'input_Name': 'Anna', 'export': 'pdf'})
        request.user = user
        request._dont_enforce_csrf_checks = True
        response = user_functions.user_functions_execute(request)
        assert response['Content-Type'] == 'application/pdf'
        assert response.content.startswith(b'%PDF')

    def test_without_export_renders_html(self, setup):
        factory, user = setup
        request = factory.get('/user_functions/execute/', {'file': 'Alle Schüler'})
        request.user = user
        with patch.object(user_functions, 'render', return_value='html') as mock_render:
            assert user_functions.user_functions_execute(request) == 'html'
        mock_render.assert_called_once()
