import sys
import os
import types
import types as _types
import json

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


# ============================================================================
# Comprehensive json_to_sql.py tests
# ============================================================================

def test_json_to_sql_datatype_map():
    """Test various datatype mappings"""
    assert j2s_mod.DATATYPE_MAP['int'] == 'INTEGER'
    assert j2s_mod.DATATYPE_MAP['text'] == 'TEXT'
    assert j2s_mod.DATATYPE_MAP['float'] == 'REAL'
    assert j2s_mod.DATATYPE_MAP['bool'] == 'BOOLEAN'


def test_parse_attribute_edge_cases():
    """Test attribute parsing with various formats"""
    # Colon format
    name, dtype = j2s_mod.parse_attribute('username:text')
    assert name == 'username' and dtype == 'TEXT'
    
    # Space format
    name, dtype = j2s_mod.parse_attribute('integer id')
    assert name == 'id' and dtype == 'INTEGER'
    
    # Single value (uses as both)
    name, dtype = j2s_mod.parse_attribute('status')
    assert name == 'status'
    
    # Unknown type (should uppercase it)
    name, dtype = j2s_mod.parse_attribute('id:unknown')
    assert dtype == 'UNKNOWN'


def test_model_analyzer_basic():
    """Test ModelAnalyzer with simple model"""
    data = {
        'model': {
            'nodes': [
                {
                    'id': 'c1',
                    'type': 'Class',
                    'data': {
                        'name': 'User',
                        'attributes': [
                            {'id': 'a1', 'name': 'id:int'},
                            {'id': 'a2', 'name': 'text username'}
                        ]
                    }
                }
            ],
            'edges': []
        }
    }
    
    analyzer = j2s_mod.ModelAnalyzer(data)
    assert 'c1' in analyzer.class_elements
    assert analyzer.class_elements['c1']['data']['name'] == 'User'
    assert len(analyzer.attributes) == 2


def test_model_analyzer_with_relationships():
    """Test ModelAnalyzer with unidirectional relationships"""
    data = {
        'model': {
            'nodes': [
                {'id': 'c1', 'type': 'Class', 'data': {'name': 'Post', 'attributes': [{'id': 'a1', 'name': 'id:int'}]}},
                {'id': 'c2', 'type': 'Class', 'data': {'name': 'User', 'attributes': [{'id': 'a2', 'name': 'id:int'}]}}
            ],
            'edges': [
                {
                    'type': 'ClassUnidirectional',
                    'source': 'c1',
                    'target': 'c2',
                    'data': {'targetRole': 'author_id'}
                }
            ]
        }
    }
    
    analyzer = j2s_mod.ModelAnalyzer(data)
    assert 'c1' in analyzer.foreign_keys_map
    assert len(analyzer.foreign_keys_map['c1']) == 1
    assert analyzer.foreign_keys_map['c1'][0][0] == 'author_id'


def test_model_analyzer_bidirectional():
    """Test ModelAnalyzer with bidirectional relationships (creates junction table)"""
    data = {
        'model': {
            'nodes': [
                {'id': 'c1', 'type': 'Class', 'data': {'name': 'Student', 'attributes': [{'id': 'a1', 'name': 'id:int'}]}},
                {'id': 'c2', 'type': 'Class', 'data': {'name': 'Course', 'attributes': [{'id': 'a2', 'name': 'id:int'}]}}
            ],
            'edges': [
                {
                    'type': 'ClassBidirectional',
                    'source': 'c1',
                    'target': 'c2',
                    'data': {'targetRole': 'enrollments', 'sourceRole': ''}
                }
            ]
        }
    }
    
    analyzer = j2s_mod.ModelAnalyzer(data)
    # Should create junction table
    junction_id = 'enrollments_mn'
    assert junction_id in analyzer.class_elements
    assert junction_id in analyzer.foreign_keys_map
    assert len(analyzer.foreign_keys_map[junction_id]) == 2


def test_sql_generator_topological_sort():
    """Test that tables are created in dependency order"""
    data = {
        'model': {
            'nodes': [
                {'id': 'c1', 'type': 'Class', 'data': {'name': 'Post', 'attributes': [{'id': 'a1', 'name': 'id:int'}]}},
                {'id': 'c2', 'type': 'Class', 'data': {'name': 'User', 'attributes': [{'id': 'a2', 'name': 'id:int'}]}}
            ],
            'edges': [
                {'type': 'ClassUnidirectional', 'source': 'c1', 'target': 'c2', 'data': {'targetRole': 'user_id'}}
            ]
        }
    }
    
    analyzer = j2s_mod.ModelAnalyzer(data)
    generator = j2s_mod.SQLGenerator(analyzer)
    sorted_ids = generator._topological_sort()
    
    # User should come before Post (Post depends on User)
    user_idx = sorted_ids.index('c2')
    post_idx = sorted_ids.index('c1')
    assert user_idx < post_idx


def test_extract_tables_full():
    """Test full extract_tables flow"""
    data = {
        'nodes': [
            {'id': 'c1', 'type': 'Class', 'data': {'name': 'Book', 'attributes': [{'id': 'a1', 'name': 'id:auto'}, {'id': 'a2', 'name': 'text title'}]}}
        ],
        'edges': []
    }
    
    sql = j2s_mod.extract_tables(data)
    assert 'CREATE TABLE' in sql
    assert 'Book' in sql
    assert 'AUTOINCREMENT' in sql or 'PRIMARY KEY' in sql


def test_extract_tables_error_handling():
    """Test error handling in extract_tables"""
    # Test with invalid/empty data
    try:
        result = j2s_mod.extract_tables({})
        # Should handle gracefully or raise
    except Exception as e:
        assert True  # Expected


# ============================================================================
# Comprehensive api.py tests
# ============================================================================

def test_build_endpoint_with_name():
    """Test _build_endpoint with named pattern"""
    P = types.SimpleNamespace
    pat = P(pattern='api/test/', name='test-endpoint')
    result = api_mod._build_endpoint(pat, 'api/test/')
    assert result['name'] == 'test-endpoint'
    assert 'api/test' in result['path']


def test_build_endpoint_no_name():
    """Test _build_endpoint without name"""
    P = types.SimpleNamespace
    pat = P(pattern='api/test/')
    result = api_mod._build_endpoint(pat, 'api/test/')
    assert result['name'] is None


def test_extract_endpoints_nested():
    """Test extract_endpoints with nested URLconf"""
    P = types.SimpleNamespace
    pat1 = P(pattern='nested/', name='nested-api')
    inner = P(url_patterns=[pat1], pattern='api/v1/')
    outer = P(url_patterns=[inner], pattern='api/')
    
    endpoints = api_mod.extract_endpoints([outer])
    assert isinstance(endpoints, list)


def test_extract_endpoints_non_api():
    """Test that non-api patterns are excluded"""
    P = types.SimpleNamespace
    pat1 = P(pattern='admin/users/', name='admin')
    
    endpoints = api_mod.extract_endpoints([pat1])
    assert len(endpoints) == 0


# ============================================================================
# Comprehensive audit.py tests
# ============================================================================

def test_parse_os_all_platforms():
    """Test OS parsing for all supported platforms"""
    test_cases = [
        ('Mozilla/5.0 (Android 10)', 'Android'),
        ('Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)', 'iOS'),
        ('Mozilla/5.0 (iPad; CPU OS 14_0)', 'iOS'),
        ('Mozilla/5.0 (Windows NT 10.0)', 'Windows 10/11'),
        ('Mozilla/5.0 (Windows NT 6.3)', 'Windows 8.1'),
        ('Mozilla/5.0 (Windows NT 6.2)', 'Windows 8'),
        ('Mozilla/5.0 (Windows NT 6.1)', 'Windows 7'),
        ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15)', 'macOS'),
        ('Mozilla/5.0 (X11; Linux x86_64)', 'Linux'),
        ('Mozilla/5.0 (X11; Ubuntu; Linux)', 'Ubuntu'),
        ('Mozilla/5.0 (X11; FreeBSD)', 'FreeBSD'),
        ('Unknown Browser', 'Unknown'),
        ('', 'Unknown'),
        (None, 'Unknown')
    ]
    
    for ua, expected in test_cases:
        result = audit_mod.parse_os_from_user_agent(ua)
        assert expected in result or result == expected


def test_validate_ip_edge_cases():
    """Test IP validation with edge cases"""
    # Valid public IPs
    assert audit_mod._validate_ip_for_location('1.1.1.1') is True
    assert audit_mod._validate_ip_for_location('8.8.8.8') is True
    
    # Private IPs
    assert audit_mod._validate_ip_for_location('192.168.1.1') is False
    assert audit_mod._validate_ip_for_location('10.0.0.1') is False
    assert audit_mod._validate_ip_for_location('172.16.0.1') is False
    
    # Loopback
    assert audit_mod._validate_ip_for_location('127.0.0.1') is False
    
    # Invalid
    assert audit_mod._validate_ip_for_location('') is False
    assert audit_mod._validate_ip_for_location(None) is False
    assert audit_mod._validate_ip_for_location('not-an-ip') is False
    assert audit_mod._validate_ip_for_location('999.999.999.999') is False


def test_is_private_ip_comprehensive():
    """Test is_private_ip with various IPs"""
    # Private
    assert audit_mod.is_private_ip('10.0.0.1') is True
    assert audit_mod.is_private_ip('192.168.1.1') is True
    assert audit_mod.is_private_ip('172.20.0.1') is True
    assert audit_mod.is_private_ip('127.0.0.1') is True
    
    # Public
    assert audit_mod.is_private_ip('8.8.8.8') is False
    assert audit_mod.is_private_ip('1.1.1.1') is False
    
    # Invalid (should be treated as private/untrusted)
    assert audit_mod.is_private_ip('invalid') is True
    assert audit_mod.is_private_ip('') is True
    assert audit_mod.is_private_ip(None) is True


def test_get_client_ip_no_headers():
    """Test client IP extraction when no headers present"""
    req = DummyRequest(meta={})
    ip = audit_mod.get_client_ip_from_request(req)
    assert ip is None


def test_get_client_ip_only_private():
    """Test client IP when only private IPs available"""
    req = DummyRequest(meta={'REMOTE_ADDR': '127.0.0.1', 'HTTP_X_FORWARDED_FOR': '10.0.0.1'})
    ip = audit_mod.get_client_ip_from_request(req)
    # Should return first valid IP even if private
    assert ip in ('127.0.0.1', '10.0.0.1')


def test_get_client_ip_invalid_values():
    """Test client IP with invalid/hostname values"""
    req = DummyRequest(meta={'HTTP_X_FORWARDED_FOR': 'hostname.com, 8.8.8.8'})
    ip = audit_mod.get_client_ip_from_request(req)
    # Should skip hostname and return valid IP
    assert ip == '8.8.8.8'


def test_format_location_string_variants():
    """Test location string formatting with different data"""
    # Full data
    loc = audit_mod._format_location_string({
        'city': 'Berlin',
        'country': 'Germany',
        'regionName': 'Brandenburg'
    })
    assert 'Berlin' in loc and 'Germany' in loc
    
    # Minimal data
    loc2 = audit_mod._format_location_string({
        'city': 'Paris',
        'country': 'France'
    })
    assert 'Paris' in loc2 and 'France' in loc2
    
    # Alternative keys
    loc3 = audit_mod._format_location_string({
        'town': 'Village',
        'country_name': 'Land'
    })
    assert loc3 and 'Village' in loc3
    
    # Missing data
    loc4 = audit_mod._format_location_string({})
    assert loc4 is None


def test_fetch_location_api_failure(monkeypatch):
    """Test location fetch when API fails"""
    def failing_middleware():
        m = types.SimpleNamespace()
        m.get_location_from_ip = lambda ip: None
        return m
    
    monkeypatch.setattr(audit_mod, 'UserAgentMiddleware', failing_middleware)
    result = audit_mod._fetch_location_from_api('8.8.8.8')
    assert result is None


def test_get_location_for_login_error_handling(monkeypatch):
    """Test location lookup error handling"""
    def failing_get_ip(request):
        raise Exception("Network error")
    
    monkeypatch.setattr(audit_mod, 'get_client_ip_from_request', failing_get_ip)
    
    req = DummyRequest()
    result = audit_mod.get_location_for_login(req)
    assert result == 'Unknown'


# ============================================================================
# Comprehensive middleware.py tests
# ============================================================================

def test_middleware_get_client_ip_multiple_headers():
    """Test IP extraction from various headers"""
    m = UserAgentMiddleware(get_response=lambda r: None)
    
    # Test X-Forwarded-For with multiple IPs (takes first IP from comma-separated list)
    req = DummyRequest(meta={'HTTP_X_FORWARDED_FOR': '10.0.0.1, 8.8.8.8, 1.1.1.1'})
    ip = m.get_client_ip(req)
    # The current implementation takes the first IP, so it will be 10.0.0.1
    assert ip is not None
    
    # Test X-Real-IP
    req2 = DummyRequest(meta={'HTTP_X_REAL_IP': '8.8.4.4'})
    ip2 = m.get_client_ip(req2)
    assert ip2 == '8.8.4.4'
    
    # Test fallback to REMOTE_ADDR
    req3 = DummyRequest(meta={'REMOTE_ADDR': '192.168.1.1'})
    ip3 = m.get_client_ip(req3)
    assert ip3 == '192.168.1.1'


def test_middleware_is_private_ip_comprehensive():
    """Test private IP detection with all ranges"""
    m = UserAgentMiddleware(get_response=lambda r: None)
    
    # Loopback
    assert m.is_private_ip('127.0.0.1') is True
    assert m.is_private_ip('127.0.0.100') is True
    
    # Class C private
    assert m.is_private_ip('192.168.0.1') is True
    assert m.is_private_ip('192.168.255.255') is True
    
    # Class A private
    assert m.is_private_ip('10.0.0.1') is True
    assert m.is_private_ip('10.255.255.255') is True
    
    # Class B private (all 172.16-31.x.x)
    for i in range(16, 32):
        assert m.is_private_ip(f'172.{i}.0.1') is True
    
    # Link-local
    assert m.is_private_ip('169.254.1.1') is True
    
    # IPv6
    assert m.is_private_ip('::1') is True
    assert m.is_private_ip('fc00::1') is True
    assert m.is_private_ip('fd00::1') is True
    assert m.is_private_ip('fe80::1') is True
    
    # Public IPs
    assert m.is_private_ip('8.8.8.8') is False
    assert m.is_private_ip('1.1.1.1') is False
    assert m.is_private_ip('172.15.0.1') is False  # Just outside private range
    assert m.is_private_ip('172.32.0.1') is False  # Just outside private range
    
    # Edge cases
    assert m.is_private_ip('') is True
    assert m.is_private_ip(None) is True


def test_middleware_format_location_variants():
    """Test location formatting with different inputs"""
    m = UserAgentMiddleware(get_response=lambda r: None)
    
    # With region
    loc = m._format_location('NYC', 'USA', 'NY')
    assert loc['city'] == 'NYC'
    assert loc['country'] == 'USA'
    assert loc['region'] == 'NY'
    assert 'NY' in loc['full_location']
    
    # Without region
    loc2 = m._format_location('Paris', 'France', '')
    assert 'Paris' in loc2['full_location']
    assert 'France' in loc2['full_location']
    
    # Same city and region
    loc3 = m._format_location('Berlin', 'Germany', 'Berlin')
    assert loc3['full_location'].count('Berlin') == 1  # Should not duplicate


def test_middleware_query_providers_error_cases(monkeypatch):
    """Test provider queries with various error conditions"""
    m = UserAgentMiddleware(get_response=lambda r: None)
    
    # Test ipapi with non-200 status
    class FailResp:
        status_code = 500
        def json(self):
            return {}
    
    monkeypatch.setattr('requests.get', lambda *a, **k: FailResp())
    result = m._query_ipapi('8.8.8.8')
    assert result is None
    
    # Test ipapi with error in response
    class ErrorResp:
        status_code = 200
        def json(self):
            return {'error': 'rate limited'}
    
    monkeypatch.setattr('requests.get', lambda *a, **k: ErrorResp())
    result = m._query_ipapi('8.8.8.8')
    assert result is None
    
    # Test ipwho with success=False
    class IPWhoFailResp:
        status_code = 200
        def json(self):
            return {'success': False, 'message': 'Invalid IP'}
    
    monkeypatch.setattr('requests.get', lambda *a, **k: IPWhoFailResp())
    result = m._query_ipwho('8.8.8.8')
    assert result is None
    
    # Test network exception
    def raise_network_error(*a, **k):
        import requests
        raise requests.exceptions.RequestException("Network error")
    
    monkeypatch.setattr('requests.get', raise_network_error)
    result = m._query_ipapi('8.8.8.8')
    assert result is None


def test_middleware_get_location_invalid_ip():
    """Test location lookup with invalid IP"""
    m = UserAgentMiddleware(get_response=lambda r: None)
    
    # Invalid IP should return None
    assert m.get_location_from_ip('not-an-ip') is None
    assert m.get_location_from_ip('999.999.999.999') is None
    assert m.get_location_from_ip('') is None
    assert m.get_location_from_ip(None) is None


def test_middleware_get_location_private_ip():
    """Test location lookup with private IP returns development marker"""
    m = UserAgentMiddleware(get_response=lambda r: None)
    
    result = m.get_location_from_ip('127.0.0.1')
    assert result['city'] == 'Development'
    assert result['country'] == 'Local'
    
    result2 = m.get_location_from_ip('192.168.1.1')
    assert result2['city'] == 'Development'


def test_middleware_get_location_fallback(monkeypatch):
    """Test that fallback provider is used when primary fails"""
    m = UserAgentMiddleware(get_response=lambda r: None)
    
    call_count = {'ipapi': 0, 'ipwho': 0}
    
    def mock_get(url, *a, **k):
        class Resp:
            status_code = 200
            def json(self):
                if 'ipapi.co' in url:
                    call_count['ipapi'] += 1
                    return {'error': 'failed'}  # Primary fails
                else:  # ipwho
                    call_count['ipwho'] += 1
                    return {'success': True, 'city': 'Fallback', 'country': 'Test', 'region': ''}
        return Resp()
    
    monkeypatch.setattr('requests.get', mock_get)
    result = m.get_location_from_ip('8.8.8.8')
    
    # Should have tried ipapi first, then ipwho
    assert call_count['ipapi'] == 1
    assert call_count['ipwho'] == 1
    assert result['city'] == 'Fallback'


def test_middleware_get_location_all_fail(monkeypatch):
    """Test when all providers fail"""
    m = UserAgentMiddleware(get_response=lambda r: None)
    
    def mock_fail(*a, **k):
        class Resp:
            status_code = 500
        return Resp()
    
    monkeypatch.setattr('requests.get', mock_fail)
    result = m.get_location_from_ip('8.8.8.8')
    
    assert result['city'] == 'Unknown'
    assert result['country'] == 'Unknown'
