from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.contrib.sessions.models import Session
from myapp.utils.audit import log_audit_event
from threading import local

# Thread-local storage to pass request between signals
_request_store = local()

def set_current_request(request):
    """Store current request in thread-local storage"""
    _request_store.request = request

def get_current_request():
    """Get current request from thread-local storage"""
    return getattr(_request_store, 'request', None)

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log when a user logs in"""
    log_audit_event(user, 'LOGIN', request)

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log when a user logs out"""
    # Check if this was a forced logout
    forced_reason = getattr(request, '_logout_reason', None)
    action = 'FORCED_LOGOUT' if forced_reason else 'LOGOUT'
    log_audit_event(user, action, request, forced_reason)
