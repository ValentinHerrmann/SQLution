from django.utils import timezone
from django.conf import settings
from myapp.models import AuditLog
import requests
from datetime import datetime
import pytz

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

def get_location_for_login(request):
    """Get location data directly during login when session might not have it yet"""
    try:
        # Get IP from request
        ip_address = get_client_ip_from_request(request)
        
        # Check if it's a private IP
        if is_private_ip(ip_address):
            return 'Development, Local'
            #return {'city': 'Development', 'country': 'Local', 'full_location': 'Development, Local'}
        
        # Fetch location from API
        response = requests.get(
            f'http://ip-api.com/json/{ip_address}?fields=status,message,country,regionName,city,timezone', 
            timeout=3
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                city = data.get('city', 'Unknown')
                country = data.get('country', 'Unknown')
                region = data.get('regionName', '')
                
                if region and region != city:
                    location_str = f"{city}, {region}, {country}"
                else:
                    location_str = f"{city}, {country}"
                
                if city != 'Unknown' and country != 'Unknown':
                    return location_str
        
        return 'Unknown'
        
    except Exception as e:
        print(f"Error getting location for login: {e}")
        return 'Unknown'

def is_private_ip(ip):
    """Check if IP is private/local"""
    if not ip:
        return True
    
    private_ranges = [
        '127.',      # Loopback
        '192.168.',  # Private Class C
        '10.',       # Private Class A
        '172.16.',   # Private Class B start
        '172.17.',   # Private Class B
        '172.18.',   # Private Class B
        '172.19.',   # Private Class B
        '172.20.',   # Private Class B
        '172.21.',   # Private Class B
        '172.22.',   # Private Class B
        '172.23.',   # Private Class B
        '172.24.',   # Private Class B
        '172.25.',   # Private Class B
        '172.26.',   # Private Class B
        '172.27.',   # Private Class B
        '172.28.',   # Private Class B
        '172.29.',   # Private Class B
        '172.30.',   # Private Class B
        '172.31.',   # Private Class B end
        '169.254.',  # Link-local
        '::1',       # IPv6 loopback
        'fc00:',     # IPv6 private
        'fd00:',     # IPv6 private
        'fe80:',     # IPv6 link-local
    ]
    
    return any(ip.startswith(prefix) for prefix in private_ranges)
