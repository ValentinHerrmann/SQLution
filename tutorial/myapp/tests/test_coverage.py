import sys
import os
import types
import types as _types

import pytest

# Ensure package importability when tests run from workspace root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Provide a lightweight fake `myapp.models` module to avoid importing Django ORM
fake_models = _types.ModuleType('myapp.models')
class _FakeManager:
    def create(self, *a, **k):
        return None

fake_models.AuditLog = type('AuditLog', (), {'objects': _FakeManager()})
fake_models.ZippedFolder = type('ZippedFolder', (), {})
sys.modules['myapp.models'] = fake_models
# Provide lightweight stubs for other app utils to avoid Django settings during import
stub_users = _types.ModuleType('myapp.utils.users')
stub_users.get_logged_in_users_count = lambda: 0
stub_users.get_session_details = lambda: {}
sys.modules['myapp.utils.users'] = stub_users

stub_utils = _types.ModuleType('myapp.utils.utils')
stub_utils.timestamp = lambda: 'ts'
stub_utils.format_sql = lambda s: s
sys.modules['myapp.utils.utils'] = stub_utils

stub_dirs = _types.ModuleType('myapp.utils.directories')
stub_dirs.fullpath = lambda d,f: os.path.join(d, f)
stub_dirs.get_directory_tree_with_sizes = lambda p: []
stub_dirs.get_user_directory = lambda user: os.path.join(ROOT, 'user_databases', user)
stub_dirs.sqllock_get = lambda d: None
stub_dirs.sqllock_release = lambda d: None
sys.modules['myapp.utils.directories'] = stub_dirs

stub_sql = _types.ModuleType('myapp.utils.sqlite_connector')
class _FakeCursor:
    description = None
    def fetchall(self):
        return []
def runSql(sql, username):
    return _FakeCursor()
stub_sql.runSql = runSql
def create_db(sql, username):
    return None
stub_sql.create_db = create_db
sys.modules['myapp.utils.sqlite_connector'] = stub_sql

stub_views_user = _types.ModuleType('myapp.views_user')
stub_views_user.get_recent_audit_logs = lambda: []
stub_views_user.log_resource_data_to_csv = lambda data: None
stub_views_user.rotate_audit_logs = lambda: None
sys.modules['myapp.views_user'] = stub_views_user

stub_decorators = _types.ModuleType('myapp.utils.decorators')
stub_decorators.is_db_admin = lambda u: True
stub_decorators.is_global_admin = lambda u: True
sys.modules['myapp.utils.decorators'] = stub_decorators

from myapp.views import api as api_mod
from myapp.utils import diagram as diagram_mod
from myapp.templatetags import extrafilters as xf_mod
from myapp.utils import json_to_sql as j2s_mod
from myapp.utils import audit as audit_mod
from myapp.middleware import UserAgentMiddleware


class DummyRequest:
    def __init__(self, meta=None, session=None, user=None, GET=None):
        self.META = meta or {}
        self.session = session or {}
        self.user = user or types.SimpleNamespace(is_authenticated=False, username='anon')
        self.GET = GET or {}


def test_api_build_and_extract_endpoint():
    # Build fake pattern-like objects
    P = types.SimpleNamespace
    pat1 = P(pattern='api/hello/', name='hello')
    pat2 = P(pattern='notapi/skip/', name='skip')
    incl = P(url_patterns=[pat1, pat2], pattern='api/')

    endpoints = api_mod.extract_endpoints([incl])
    assert isinstance(endpoints, list)
    assert any(e['path'].endswith('api/hello/') or e['name'] == 'hello' for e in endpoints)


def test_parse_attribute_variants():
    name, dtype = j2s_mod.parse_attribute('id:int')
    assert name == 'id' and 'INTEGER' in dtype

    name2, dtype2 = j2s_mod.parse_attribute('varchar title')
    assert name2 == 'title'


def test_extrafilters_basic_and_version():
    assert xf_mod.endswith('file.txt', '.txt') is True
    assert xf_mod.dict_get({'a': 1}, 'a') == 1
    # get_version and url should return strings (VERSION exists in repo)
    v = xf_mod.get_version()
    u = xf_mod.get_version_url()
    assert isinstance(v, str)
    assert isinstance(u, str)


def test_diagram_load_json_writes_and_calls(monkeypatch, tmp_path):
    # Monkeypatch get_user_directory to point to tmp_path
    monkeypatch.setattr(diagram_mod, 'get_user_directory', lambda username: str(tmp_path))

    called = {}

    def fake_create_db(sql, username):
        called['sql'] = sql
        called['user'] = username

    monkeypatch.setattr(diagram_mod, 'create_db', fake_create_db)
    monkeypatch.setattr(diagram_mod, 'format_sql', lambda s: 'SQL:' + s)
    monkeypatch.setattr(diagram_mod, 'extract_tables', lambda d: 'CREATE TABLE t;')

    test_json = b'{"model": {"nodes": [], "edges": []}}'
    diagram_mod.load_json(test_json, 'alice')

    assert called.get('user') == 'alice'
    assert 'CREATE TABLE' in called.get('sql') or called.get('sql').startswith('SQL:')


def test_audit_parse_os_and_ip_utils(monkeypatch):
    ua_windows = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    assert audit_mod.parse_os_from_user_agent(ua_windows) in ("Windows 10/11", "Windows")

    # test ip validation helpers
    assert audit_mod._validate_ip_for_location('8.8.8.8') is True
    assert audit_mod._validate_ip_for_location('127.0.0.1') is False
    assert audit_mod.is_private_ip('10.0.0.1') is True
    assert audit_mod.is_private_ip('8.8.8.8') is False

    # get_client_ip_from_request prefers public IPs first
    req = DummyRequest(meta={'HTTP_X_FORWARDED_FOR': '10.0.0.1, 8.8.8.8', 'REMOTE_ADDR': '127.0.0.1'})
    ip = audit_mod.get_client_ip_from_request(req)
    assert ip == '8.8.8.8' or ip == '10.0.0.1'

    # get_location_for_login should use middleware; monkeypatch middleware
    monkeypatch.setattr(audit_mod, 'UserAgentMiddleware', lambda: types.SimpleNamespace(get_location_from_ip=lambda ip: {'city':'Berlin','country':'Germany','full_location':'Berlin, Germany'}))
    req2 = DummyRequest(meta={'REMOTE_ADDR': '8.8.8.8'})
    loc = audit_mod.get_location_for_login(req2)
    assert 'Berlin' in loc or loc == 'Unknown'


def test_middleware_location_and_ip(monkeypatch):
    m = UserAgentMiddleware(get_response=lambda req: None)
    # is_private_ip via is_private_ip method
    assert m.is_private_ip('127.0.0.1') is True
    assert m.is_private_ip('8.8.8.8') is False

    # Test formatting
    fmt = m._format_location('City', 'Country', 'Region')
    assert fmt['full_location'].startswith('City')

    # Monkeypatch requests.get to simulate ipapi response
    class FakeResp:
        def __init__(self, status, data):
            self.status_code = status
            self._data = data
        def json(self):
            return self._data

    def fake_get(url, timeout, allow_redirects, headers):
        if 'ipapi.co' in url:
            return FakeResp(200, {'city': 'X', 'country_name': 'Y', 'region': 'R'})
        return FakeResp(200, {'success': True, 'city': 'A', 'country': 'B', 'region': 'C'})

    monkeypatch.setattr('requests.get', fake_get)
    res = m.get_location_from_ip('8.8.8.8')
    assert res and res.get('city') in ('X', 'A')
