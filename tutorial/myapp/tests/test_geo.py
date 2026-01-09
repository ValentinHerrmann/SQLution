import pytest
import sys
import types

# Provide a lightweight fake `myapp.models` to avoid importing Django during tests
if 'myapp.models' not in sys.modules:
    fake_mod = types.ModuleType('myapp.models')
    class _FakeManager:
        @staticmethod
        def create(*a, **k):
            return None
    class _FakeAuditLog:
        objects = _FakeManager()
    fake_mod.AuditLog = _FakeAuditLog
    sys.modules['myapp.models'] = fake_mod

from myapp.middleware import UserAgentMiddleware
from myapp.utils.audit import get_client_ip_from_request, _fetch_location_from_api


class DummyResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


class DummyRequest:
    def __init__(self, meta=None, get_params=None):
        self.META = meta or {}
        self.GET = get_params or {}


def test_middleware_ipapi_success(monkeypatch):
    """ipapi.co primary provider returns formatted location"""
    payload = {'city': 'Berlin', 'country_name': 'Germany', 'region': 'Berlin'}

    def fake_get(url, timeout=None, allow_redirects=None, headers=None):
        assert 'ipapi.co' in url
        return DummyResponse(status_code=200, payload=payload)

    monkeypatch.setattr('myapp.middleware.requests.get', fake_get)

    middleware = UserAgentMiddleware(get_response=lambda req: None)
    out = middleware.get_location_from_ip('1.2.3.4')
    assert out['city'] == 'Berlin'
    assert out['country'] == 'Germany'
    assert 'Berlin' in out['full_location']


def test_middleware_fallback_ipwho(monkeypatch):
    """When ipapi fails, ipwho.is is used as fallback"""
    # First call (ipapi) returns an error payload
    calls = {'n': 0}

    def fake_get(url, timeout=None, allow_redirects=None, headers=None):
        calls['n'] += 1
        if 'ipapi.co' in url:
            return DummyResponse(status_code=200, payload={'error': True})
        if 'ipwho.is' in url:
            return DummyResponse(status_code=200, payload={'success': True, 'city': 'Paris', 'country': 'France', 'region': 'Ile-de-France'})
        return DummyResponse(status_code=404)

    monkeypatch.setattr('myapp.middleware.requests.get', fake_get)
    middleware = UserAgentMiddleware(get_response=lambda req: None)
    out = middleware.get_location_from_ip('8.8.8.8')
    assert out['city'] == 'Paris'
    assert out['country'] == 'France'


def test_middleware_invalid_ip_returns_none():
    middleware = UserAgentMiddleware(get_response=lambda req: None)
    assert middleware.get_location_from_ip('not-an-ip') is None


def test_middleware_private_ip_development():
    middleware = UserAgentMiddleware(get_response=lambda req: None)
    # loopback should return development marker
    out = middleware.get_location_from_ip('127.0.0.1')
    assert out['city'] == 'Development'


def test_get_client_ip_from_request_prefers_public():
    # header contains private then public IP; expect public returned
    req = DummyRequest(meta={'HTTP_X_FORWARDED_FOR': '192.168.1.5, 8.8.4.4'})
    ip = get_client_ip_from_request(req)
    assert ip == '8.8.4.4'


def test_get_client_ip_from_request_hostname_ignored():
    # hostname in header should be ignored and valid IP returned
    req = DummyRequest(meta={'HTTP_X_REAL_IP': 'bad.hostname.example,10.0.0.5'})
    ip = get_client_ip_from_request(req)
    assert ip == '10.0.0.5'


def test_fetch_location_from_api_uses_middleware(monkeypatch):
    # Ensure audit._fetch_location_from_api uses middleware.get_location_from_ip
    from myapp.utils import audit as audit_module

    def fake_get_location(ip):
        return {'full_location': 'TestCity, TestCountry'}

    # Replace the class with a dummy that accepts no args and implements the method
    class DummyMiddleware:
        def __init__(self, *a, **k):
            pass
        def get_location_from_ip(self, ip):
            return fake_get_location(ip)

    monkeypatch.setattr(audit_module, 'UserAgentMiddleware', DummyMiddleware)
    res = _fetch_location_from_api('1.1.1.1')
    assert res == 'TestCity, TestCountry'
