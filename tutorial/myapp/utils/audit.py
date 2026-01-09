from django.utils import timezone
from django.conf import settings
from myapp.models import AuditLog
import requests
import ipaddress
from datetime import datetime
import pytz
from myapp.middleware import UserAgentMiddleware

def log_audit_event(user, action, request=None, forced_reason=None):
    """
    Log an audit event for login/logout actions
    
    Args:
        user: Django User object
        action: One of 'LOGIN', 'LOGOUT', 'FORCED_LOGOUT', 'SESSION_TIMEOUT'
        request: Django request object (optional, for IP/location/OS detection)
        forced_reason: Reason for forced logout (optional)
    """
    try:
        ip_address = None
        operating_system = None
        location = None
        session_id = None
        
        if request:
            # Get IP address
            ip_address = request.session.get('client_ip') or get_client_ip_from_request(request)
            
            # Get session ID
            session_id = request.session.session_key
            
            # Get OS info
            user_agent_str = request.META.get('HTTP_USER_AGENT', '')
            if user_agent_str:
                operating_system = parse_os_from_user_agent(user_agent_str)
            
            # Get location info
            location_data = request.session.get('location', {})
            if isinstance(location_data, dict) and len(location_data) > 0:
                city = location_data.get('city', 'Unknown')
                country = location_data.get('country', 'Unknown')
                full_location = location_data.get('full_location')
                
                if full_location:
                    location = full_location
                elif city != 'Unknown' and country != 'Unknown':
                    location = f"{city}, {country}"
                elif city != 'Unknown':
                    location = city
                elif country != 'Unknown':
                    location = country
                else:
                    if action == 'LOGIN':
                        location = get_location_for_login(request)
                    else:
                        location = 'Unknown'
            else:
                # If no location data in session (e.g., during login), try to get it directly
                if action == 'LOGIN':
                    location = get_location_for_login(request)
                else:
                    location = 'Unknown'
        
        # Create audit log entry with server local time
        local_tz = pytz.timezone(settings.TIME_ZONE)  # Get timezone from Django settings
        local_time = datetime.now(local_tz)
        
        AuditLog.objects.create(
            user=user if user and hasattr(user, 'id') else None,
            username=user.username if user and hasattr(user, 'username') else 'Unknown',
            action=action,
            ip_address=ip_address,
            operating_system=operating_system,
            location=location,
            session_id=session_id,
            forced_reason=forced_reason,
            timestamp=local_time
        )
        
        print(f"Audit log created: {user.username if user else 'Unknown'} - {action}")
        
    except Exception as e:
        print(f"Error creating audit log: {e}")

def get_client_ip_from_request(request):
    """Extract client IP from request headers and ensure it's a valid IP (not a hostname)."""
    headers_to_check = [
        'HTTP_X_FORWARDED_FOR',
        'HTTP_X_REAL_IP',
        'HTTP_X_FORWARDED',
        'HTTP_X_CLUSTER_CLIENT_IP',
        'HTTP_FORWARDED_FOR',
        'HTTP_FORWARDED',
        'REMOTE_ADDR'
    ]
    # Helper functions (module-level small helpers would be ideal; kept local to keep file scope tidy)
    def _parse_candidates(raw):
        return [p.strip() for p in raw.split(',') if p and p.strip()]

    def _is_valid_ip(candidate):
        try:
            ipaddress.ip_address(candidate)
            return True
        except ValueError:
            return False

    def _is_public_ip(candidate):
        try:
            ip_obj = ipaddress.ip_address(candidate)
            return not (ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved)
        except ValueError:
            return False

    # Collect candidates from headers in order
    candidates = []
    for header in headers_to_check:
        raw = request.META.get(header)
        if not raw:
            continue
        candidates.extend(_parse_candidates(raw))

    # Prefer the first public IP
    for c in candidates:
        if _is_public_ip(c):
            return c

    # Otherwise return the first valid IP (may be private)
    for c in candidates:
        if _is_valid_ip(c):
            return c

    return None

def parse_os_from_user_agent(user_agent):
    """Parse OS from user agent string"""
    if not user_agent:
        return "Unknown"
    
    user_agent = user_agent.lower()
    
    # Check for mobile platforms first
    if 'android' in user_agent:
        return "Android"
    elif 'iphone' in user_agent or 'ipad' in user_agent:
        return "iOS"
    
    # Check for desktop platforms
    elif 'windows nt 10' in user_agent:
        return "Windows 10/11"
    elif 'windows nt 6.3' in user_agent:
        return "Windows 8.1"
    elif 'windows nt 6.2' in user_agent:
        return "Windows 8"
    elif 'windows nt 6.1' in user_agent:
        return "Windows 7"
    elif 'windows' in user_agent:
        return "Windows"
    elif 'mac os x' in user_agent or 'macos' in user_agent:
        return "macOS"
    elif 'linux' in user_agent:
        if 'ubuntu' in user_agent:
            return "Ubuntu"
        else:
            return "Linux"
    elif 'freebsd' in user_agent:
        return "FreeBSD"
    else:
        return "Unknown"

def _validate_ip_for_location(ip_address):
    """Validate IP and check if it's private/local. Returns True if IP is valid and public."""
    if not ip_address:
        return False
    
    try:
        ip_obj = ipaddress.ip_address(ip_address)
        return not (ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved)
    except ValueError:
        return False

def _fetch_location_from_api(ip_address):
    """Fetch location from IP geolocation API. Returns location string or None."""
    try:
        # Reuse middleware's location lookup (which already prefers HTTPS providers)
        middleware = UserAgentMiddleware()
        data = middleware.get_location_from_ip(ip_address)
        if not data:
            return None

        # If middleware returned a full formatted location, use it
        full = data.get('full_location')
        if full:
            return full

        # Otherwise normalize and format
        return _format_location_string(data)
    except Exception:
        return None

def _format_location_string(data):
    """Format location data into a location string."""
    # Accept multiple key names depending on provider
    city = data.get('city') or data.get('town') or data.get('village') or 'Unknown'
    country = data.get('country') or data.get('country_name') or 'Unknown'
    region = data.get('regionName') or data.get('region') or data.get('region_name') or ''

    if not city or city == 'Unknown' or not country or country == 'Unknown':
        return None

    if region and region != city:
        return f"{city}, {region}, {country}"
    return f"{city}, {country}"

def get_location_for_login(request):
    """Get location data directly during login when session might not have it yet"""
    try:
        ip_address = get_client_ip_from_request(request)
        
        if not _validate_ip_for_location(ip_address):
            return 'Unknown'
        
        location = _fetch_location_from_api(ip_address)
        return location or 'Unknown'
        
    except Exception as e:
        print(f"Error getting location for login: {e}")
        return 'Unknown'
    
def is_private_ip(ip):
    """Check if IP is private/local"""
    if not ip:
        return True
    
    try:
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved
    except ValueError:
        # Treat invalid/non-IP input as private/untrusted
        return True
