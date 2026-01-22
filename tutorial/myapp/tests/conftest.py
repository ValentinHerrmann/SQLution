"""
pytest configuration for Django tests.
"""
import django
import os
import sys
from pathlib import Path
from django.conf import settings
import pytest
from unittest.mock import patch

# Add the tutorial directory to the Python path
# This allows Django to find the tutorial.settings module
tutorial_dir = Path(__file__).resolve().parent.parent.parent.parent / 'tutorial'
sys.path.insert(0, str(tutorial_dir))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tutorial.settings')

# Setup Django
django.setup()

# Configure ALLOWED_HOSTS for testing
if not hasattr(settings, 'ALLOWED_HOSTS'):
    settings.ALLOWED_HOSTS = []
# Add testserver and common test hosts
test_hosts = ['testserver', 'localhost', '127.0.0.1', 'example.com']
for host in test_hosts:
    if host not in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS.append(host)


@pytest.fixture
def rf():
    """
    RequestFactory fixture that sets SERVER_NAME to avoid DisallowedHost errors.
    Usage: rf.get('/path'), rf.post('/path'), etc.
    """
    from django.test import RequestFactory
    
    class ConfiguredRequestFactory(RequestFactory):
        """RequestFactory with default SERVER_NAME set."""
        def request(self, **request_kwargs):
            if 'SERVER_NAME' not in request_kwargs:
                request_kwargs['SERVER_NAME'] = 'testserver'
            return super().request(**request_kwargs)
    
    return ConfiguredRequestFactory()


@pytest.fixture(autouse=True)
def bypass_auth_decorators():
    """
    Automatically bypass Django authentication decorators for all tests.
    This allows tests using RequestFactory to work without full middleware stack.
    """
    with patch('django.contrib.auth.decorators.login_required', lambda f: f), \
         patch('django.contrib.auth.decorators.user_passes_test', lambda test_func, **kwargs: lambda f: f):
        yield
