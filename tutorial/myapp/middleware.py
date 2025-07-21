from django.utils.deprecation import MiddlewareMixin
import requests
import json

class UserAgentMiddleware(MiddlewareMixin):
    """Middleware to capture user agent and IP information in session"""
    
    def get_client_ip(self, request):
        """Get the real client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_location_from_ip(self, ip):
        """Get location information from IP address using a free geolocation service"""
        try:
            # Skip private/local IPs
            if ip in ['127.0.0.1', '::1'] or ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.'):
                return {'city': 'Local', 'country': 'Local'}
            
            # Use ip-api.com (free service, no API key required)
            response = requests.get(f'http://ip-api.com/json/{ip}', timeout=2)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return {
                        'city': data.get('city', 'Unknown'),
                        'country': data.get('country', 'Unknown'),
                        'region': data.get('regionName', ''),
                    }
        except Exception:
            pass
        
        return {'city': 'Unknown', 'country': 'Unknown'}
    
    def process_request(self, request):
        if request.user.is_authenticated and hasattr(request, 'session'):
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            client_ip = self.get_client_ip(request)
            
            if user_agent:
                request.session['user_agent'] = user_agent
            
            if client_ip:
                request.session['client_ip'] = client_ip
                
                # Only fetch location if we don't have it yet or IP changed
                if request.session.get('client_ip') != client_ip or 'location' not in request.session:
                    location = self.get_location_from_ip(client_ip)
                    request.session['location'] = location
        
        return None
