from django.utils.deprecation import MiddlewareMixin
import requests
import json
import ipaddress

class UserAgentMiddleware(MiddlewareMixin):
    """Middleware to capture user agent and IP information in session"""
    
    def get_client_ip(self, request):
        """Get the real client IP address"""
        # Check various headers that might contain the real IP
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
                # Handle comma-separated IPs (from proxies)
                if ',' in ip:
                    ip = ip.split(',')[0].strip()
                
                # Skip private/local IPs and look for public ones
                if not self.is_private_ip(ip):
                    return ip
        
        # If no public IP found, return the first available IP
        for header in headers_to_check:
            ip = request.META.get(header)
            if ip:
                if ',' in ip:
                    ip = ip.split(',')[0].strip()
                return ip
        
        return '127.0.0.1'  # Fallback
    
    def is_private_ip(self, ip):
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

    def _format_location(self, city, country, region=''):
        """Normalize fields and return the dict shape used by the app."""
        city = city or 'Unknown'
        country = country or 'Unknown'
        region = region or ''

        if region and region != city:
            full = f"{city}, {region}, {country}"
        else:
            full = f"{city}, {country}"

        return {
            'city': city,
            'country': country,
            'region': region,
            'full_location': full
        }

    def _query_ipapi(self, ip):
        """Query ipapi.co over HTTPS. Return formatted dict or None."""
        try:
            url = f'https://ipapi.co/{ip}/json/'
            resp = requests.get(url, timeout=3, allow_redirects=False, headers={'User-Agent': 'SQLution-Middleware/1.0'})
            if resp.status_code != 200:
                return None
            data = resp.json()
            if data.get('error'):
                return None
            return self._format_location(
                data.get('city'),
                data.get('country_name'),
                data.get('region')
            )
        except requests.exceptions.RequestException:
            return None

    def _query_ipwho(self, ip):
        """Query ipwho.is over HTTPS. Return formatted dict or None."""
        try:
            url = f'https://ipwho.is/{ip}'
            resp = requests.get(url, timeout=3, allow_redirects=False, headers={'User-Agent': 'SQLution-Middleware/1.0'})
            if resp.status_code != 200:
                return None
            data = resp.json()
            if data.get('success') is False:
                return None
            return self._format_location(
                data.get('city'),
                data.get('country'),
                data.get('region')
            )
        except requests.exceptions.RequestException:
            return None
    
    def get_location_from_ip(self, ip):
        """Get location information from IP address using a free geolocation service"""
        # Validate IP format first to avoid constructing URLs from untrusted input
        if not ip:
            return None

        try:
            # This will raise ValueError for invalid or non-IP input
            ip_obj = ipaddress.ip_address(ip)
        except ValueError:
            # Invalid IP — do not use it to construct external URLs
            return None

        # Development/local IP short-circuit
        if self.is_private_ip(ip):
            return {'city': 'Development', 'country': 'Local'}

        # Try primary provider
        result = self._query_ipapi(ip)
        if result:
            return result

        # Try fallback provider
        result = self._query_ipwho(ip)
        if result:
            return result

        # If everything fails, return unknown location
        return {'city': 'Unknown', 'country': 'Unknown', 'full_location': 'Unknown'}
    
    def process_request(self, request):
        if request.user.is_authenticated and hasattr(request, 'session'):
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            client_ip = self.get_client_ip(request)
            
            # Debug: Print all relevant headers (remove in production)
            debug_headers = {
                'REMOTE_ADDR': request.META.get('REMOTE_ADDR'),
                'HTTP_X_FORWARDED_FOR': request.META.get('HTTP_X_FORWARDED_FOR'),
                'HTTP_X_REAL_IP': request.META.get('HTTP_X_REAL_IP'),
                'HTTP_X_FORWARDED': request.META.get('HTTP_X_FORWARDED'),
            }
            print(f"IP Debug for user {request.user.username}: {debug_headers} -> Detected IP: {client_ip}")
            
            # For development/testing: override with a real IP to test geolocation
            # Remove this in production or make it configurable
            if client_ip == '127.0.0.1' and hasattr(request, 'GET') and request.GET.get('test_ip'):
                test_ip = request.GET.get('test_ip')
                print(f"Using test IP: {test_ip}")
                client_ip = test_ip
            
            if user_agent:
                request.session['user_agent'] = user_agent
            
            if client_ip:
                # Always update IP in session
                request.session['client_ip'] = client_ip
                
                # Only fetch location if IP changed or no location data exists
                stored_ip = request.session.get('stored_ip_for_location')
                if stored_ip != client_ip or 'location' not in request.session:
                    print(f"Fetching location for IP: {client_ip}")
                    location = self.get_location_from_ip(client_ip)
                    request.session['location'] = location
                    request.session['stored_ip_for_location'] = client_ip
                    print(f"Location result: {location}")
        
        # Store request for signal handlers
        from myapp.signals import set_current_request
        set_current_request(request)
        
        return None
