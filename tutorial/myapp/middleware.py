from django.utils.deprecation import MiddlewareMixin
import requests
import json

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
    
    def get_location_from_ip(self, ip):
        """Get location information from IP address using a free geolocation service"""
        try:
            # For development: if it's a private/local IP, simulate location or use a public IP for testing
            if self.is_private_ip(ip):
                # In development, you might want to test with a real IP
                # For now, we'll return a development indicator
                return {'city': 'Development', 'country': 'Local'}
            
            # Use ip-api.com (free service, no API key required)
            # Limit: 1000 requests per month for free tier
            response = requests.get(
                f'http://ip-api.com/json/{ip}?fields=status,message,country,regionName,city,timezone', 
                timeout=3
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    city = data.get('city', 'Unknown')
                    country = data.get('country', 'Unknown')
                    region = data.get('regionName', '')
                    
                    # Provide more detailed location if available
                    if region and region != city:
                        location_str = f"{city}, {region}, {country}"
                    else:
                        location_str = f"{city}, {country}"
                    
                    return {
                        'city': city,
                        'country': country,
                        'region': region,
                        'full_location': location_str
                    }
                else:
                    # API returned an error
                    print(f"IP-API error for {ip}: {data.get('message', 'Unknown error')}")
            else:
                print(f"HTTP error {response.status_code} when querying location for {ip}")
                
        except requests.exceptions.Timeout:
            print(f"Timeout when querying location for {ip}")
        except requests.exceptions.RequestException as e:
            print(f"Request error when querying location for {ip}: {e}")
        except Exception as e:
            print(f"Unexpected error when querying location for {ip}: {e}")
        
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
        
        return None
