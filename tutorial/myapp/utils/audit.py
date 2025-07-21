from django.utils import timezone
from myapp.models import AuditLog

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
        user_agent = None
        
        if request:
            # Get IP address
            ip_address = request.session.get('client_ip') or get_client_ip_from_request(request)
            
            # Get OS info
            user_agent_str = request.META.get('HTTP_USER_AGENT', '')
            if user_agent_str:
                user_agent = user_agent_str
                operating_system = parse_os_from_user_agent(user_agent_str)
            
            # Get location info
            location_data = request.session.get('location', {})
            if isinstance(location_data, dict):
                location = location_data.get('full_location') or f"{location_data.get('city', 'Unknown')}, {location_data.get('country', 'Unknown')}"
        
        # Create audit log entry
        AuditLog.objects.create(
            user=user if user and hasattr(user, 'id') else None,
            username=user.username if user and hasattr(user, 'username') else 'Unknown',
            action=action,
            ip_address=ip_address,
            operating_system=operating_system,
            location=location,
            user_agent=user_agent,
            forced_reason=forced_reason
        )
        
        print(f"Audit log created: {user.username if user else 'Unknown'} - {action}")
        
    except Exception as e:
        print(f"Error creating audit log: {e}")

def get_client_ip_from_request(request):
    """Extract client IP from request headers"""
    headers_to_check = [
        'HTTP_X_FORWARDED_FOR',
        'HTTP_X_REAL_IP',
        'HTTP_X_FORWARDED',
        'HTTP_X_CLUSTER_CLIENT_IP',
        'HTTP_FORWARDED_FOR',
        'HTTP_FORWARDED',
        'REMOTE_ADDR'
    ]
    
    for header in headers_to_check:
        ip = request.META.get(header)
        if ip:
            if ',' in ip:
                ip = ip.split(',')[0].strip()
            return ip
    
    return '127.0.0.1'

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
