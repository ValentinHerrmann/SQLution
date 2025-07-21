
import pprint
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.db import connection, DatabaseError
from django.apps import apps
import form_designer
import shutil
import psutil
import csv
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.utils import timezone

from .views_helpers import is_global_admin

from .forms import SQLQueryForm,UploadFileForm
from .models import *
from .utils import *  # Assuming you have this function in utils.py
from .sqlite_connector import *  # Import sqlite3 for SQLite database connection
import json
from datetime import datetime
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test

from django.shortcuts import redirect
from django.contrib.auth import logout
import os
import re

def timestamp():
    return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]") + "\t"

def get_logged_in_users_count():
    """Get the number of currently logged in users - now with working logic"""
    try:
        from django.contrib.auth.models import User
        from datetime import timedelta
        
        # Get current time
        current_time = timezone.now()
        
        # Clean up expired sessions first (this might help with accuracy)
        try:
            expired_sessions = Session.objects.filter(expire_date__lt=current_time)
            expired_count = expired_sessions.count()
            if expired_count > 0:
                expired_sessions.delete()
                print(f"{timestamp()}Cleaned up {expired_count} expired sessions")
        except Exception as e:
            print(f"Session cleanup failed: {e}")
        
        # Get all sessions that haven't expired yet
        active_sessions = Session.objects.filter(expire_date__gte=current_time)
        
        # Count unique logged-in users from active sessions
        logged_in_user_ids = set()
        valid_sessions = 0
        
        for session in active_sessions:
            try:
                session_data = session.get_decoded()
                user_id = session_data.get('_auth_user_id')
                
                # Only count if there's actually a user ID
                if user_id:
                    try:
                        # Verify the user exists and is active
                        user = User.objects.get(id=user_id, is_active=True)
                        logged_in_user_ids.add(user_id)
                        valid_sessions += 1
                    except User.DoesNotExist:
                        continue
                        
            except Exception:
                # Skip sessions that can't be decoded
                continue
        
        user_count = len(logged_in_user_ids)
        total_users = User.objects.filter(is_active=True).count()
        
        print(f"{timestamp()}Active sessions: {active_sessions.count()}")
        print(f"{timestamp()}Valid sessions with users: {valid_sessions}")
        print(f"{timestamp()}Unique logged-in users: {user_count}")
        print(f"{timestamp()}Total users in system: {total_users}")
        
        # Additional validation: if the count seems too high, use an alternative method
        if user_count > total_users:
            print(f"{timestamp()}WARNING: Count too high, using total users as fallback")
            return total_users
        
        # If count is 0 but we have sessions, there might be an issue
        if user_count == 0 and active_sessions.count() > 0:
            print(f"{timestamp()}WARNING: No users found but sessions exist, investigating...")
            # Try a simpler count
            simple_count = 0
            for session in active_sessions[:5]:  # Check first 5 sessions
                try:
                    session_data = session.get_decoded()
                    print(f"{timestamp()}Session data keys: {list(session_data.keys())}")
                    if '_auth_user_id' in session_data:
                        simple_count += 1
                except Exception as e:
                    print(f"{timestamp()}Session decode error: {e}")
            
            if simple_count > 0:
                print(f"{timestamp()}Found {simple_count} sessions with auth data")
                return min(simple_count, total_users)
        
        return user_count
        
    except Exception as e:
        print(f"Error counting logged in users: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return 0

def log_resource_data_to_csv(data):
    """Log resource data to CSV file"""
    try:
        # Use multiple possible paths for the CSV file
        possible_paths = [
            os.path.join(os.getcwd(), 'resource_logs.csv'),  # Current directory (tutorial/myapp)
            os.path.join(os.path.dirname(os.getcwd()), 'resource_logs.csv'),  # Parent directory (tutorial)
            os.path.join(os.path.dirname(os.path.dirname(os.getcwd())), 'resource_logs.csv'),  # Project root
        ]
        
        csv_file_path = None
        for path in possible_paths:
            try:
                # Try to create/write to this path
                test_dir = os.path.dirname(path)
                if os.path.exists(test_dir) and os.access(test_dir, os.W_OK):
                    csv_file_path = path
                    break
            except:
                continue
        
        if csv_file_path is None:
            # Fallback to current directory
            csv_file_path = os.path.join(os.getcwd(), 'resource_logs.csv')
        
        file_exists = os.path.isfile(csv_file_path)
        
        with open(csv_file_path, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'timestamp', 'logged_in_users', 'fullness_percentage', 'total_gb', 'used_gb', 'free_gb',
                'ram_total', 'ram_used', 'ram_free', 'ram_percentage', 'cpu_percentage'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header if file is new
            if not file_exists:
                writer.writeheader()
            
            # Write the data
            csv_data = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'logged_in_users': data.get('logged_in_users', 0),
                'fullness_percentage': data.get('fullness_percentage', 0),
                'total_gb': data.get('total_gb', 0),
                'used_gb': data.get('used_gb', 0),
                'free_gb': data.get('free_gb', 0),
                'ram_total': data.get('ram_total', 0),
                'ram_used': data.get('ram_used', 0),
                'ram_free': data.get('ram_free', 0),
                'ram_percentage': data.get('ram_percentage', 0),
                'cpu_percentage': data.get('cpu_percentage', 0)
            }
            writer.writerow(csv_data)
            
        print(f"Successfully logged resource data to: {csv_file_path}")
            
    except Exception as e:
        print(f"Error logging resource data to CSV: {e}")
        # Try to log the error details for debugging
        import traceback
        print(f"Full error details: {traceback.format_exc()}")

@login_required
def logged_in(request):
    user = request.user.username
    print(timestamp() + "Logged in: " + user)
    if user == 'admin':
        pass#return redirect('admin')  # Redirect to the admin page
    #restore_zip_to_directory(get_user_directory(user))
    return redirect('home')  # Redirect to the home page after login


@csrf_protect
@require_http_methods(["GET", "POST"])
def logged_out(request):
    user = request.user.username if request.user.is_authenticated else ''
    if user == '':
        user = request.GET.get("user") 
    if user is not None and user != '':
        print(timestamp() + "Logged out: " + user)
        #zip_and_save_directory(get_user_directory(user))
    
    if request.user.is_authenticated:
        logout(request)  # Log out the user
    
    request.session.flush()  # Clear the session data
    return redirect('/accounts/login')  # Redirect to the login page
    

@login_required
@user_passes_test(is_global_admin)
@csrf_protect  
def admin_overview(request):  
    restart = request.POST.get("restart") or request.GET.get("restart")
    if restart == 'true':
        if request.user.is_authenticated:
            logout(request)
        request.session.flush()
        os.system("cd .. && ./update_and_launch.sh")

    rate = os.getenv('RESOURCES_REFRESH', default=5000)

    last_launched = ""
    try:
        with open('last_launched.txt', 'r') as f:
            last_launched = f.read().strip()
    except FileNotFoundError:
        # If the file doesn't exist, create it with the current timestamp
        with open('last_launched.txt', 'w') as f:
            last_launched = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(last_launched)

    return render(request, 'admin_overview.html', {
        'refresh_rate': rate,
        'commit': os.popen('git log -1 --pretty=%B').read().strip(),
        'last_launched': last_launched,
        'wdir': os.getcwd(),
        'logged_in_users': get_logged_in_users_count(),  # Add initial logged-in users count
        #'users': user_data,
        #"fullness_percentage": int(round(fullness_percentage, 0)),
        #"total_gb": total_gb,
        #"used_gb": used_gb,
        #"free_gb": free_gb,
        #"ram_total": ram_total,
        #"ram_used": ram_used,
        #"ram_free": ram_free,
        #"ram_percentage": int(round(ram_percentage, 0)),
        #"cpu_percentage": int(round(cpu_percentage, 0)),
    })


@login_required
@user_passes_test(is_global_admin)
def get_system_data(request):
    print(f"{timestamp()}get_system_data endpoint called by {request.user.username}")

    # Get user databases directory information
    try:
        user_databases_path = os.path.join(os.getcwd(), 'user_databases')
        user_data = get_directory_tree_with_sizes(user_databases_path)
    except Exception as e:
        print(f"Error getting user directory data: {e}")
        user_data = []

    # Get system drive usage - use the current drive on Windows
    try:
        if os.name == 'nt':  # Windows
            # Get the drive of the current working directory
            current_drive = os.path.splitdrive(os.getcwd())[0] + os.sep
            total, used, free = shutil.disk_usage(current_drive)
        else:  # Unix/Linux
            total, used, free = shutil.disk_usage("/")
        
        fullness_percentage = (used / total) * 100
    except Exception as e:
        print(f"Error getting disk usage: {e}")
        total, used, free = 0, 0, 0
        fullness_percentage = 0

    # Convert absolute values to GB for readability
    total_gb = round(total / (1000 ** 3), 2)
    used_gb = round(used / (1000 ** 3), 2)
    free_gb = round(free / (1000 ** 3), 2)

    # Get RAM usage
    try:
        ram = psutil.virtual_memory()
        ram_total = round(ram.total / (1000 ** 3), 2)
        ram_used = round(ram.used / (1000 ** 3), 2)
        ram_free = round(ram.available / (1000 ** 3), 2)
        ram_percentage = ram.percent
    except Exception as e:
        print(f"Error getting RAM usage: {e}")
        ram_total = ram_used = ram_free = ram_percentage = 0

    # Get CPU usage
    try:
        cpu_percentage = psutil.cpu_percent(0.5)
    except Exception as e:
        print(f"Error getting CPU usage: {e}")
        cpu_percentage = 0

    # Get logged-in users count
    logged_in_users = get_logged_in_users_count()
    print(f"{timestamp()}Returning logged_in_users count: {logged_in_users}")

    # Prepare response data
    response_data = {
        'directories': user_data,
        "fullness_percentage": int(round(fullness_percentage, 0)),
        "total_gb": total_gb,
        "used_gb": used_gb,
        "free_gb": free_gb,
        "ram_total": ram_total,
        "ram_used": ram_used,
        "ram_free": ram_free,
        "ram_percentage": int(round(ram_percentage, 0)),
        "cpu_percentage": int(round(cpu_percentage, 0)),
        "logged_in_users": logged_in_users,
    }

    # Log data to CSV
    print(f"{timestamp()}Attempting to log resource data to CSV...")
    log_resource_data_to_csv(response_data)
    print(f"{timestamp()}CSV logging completed.")

    # Return data as JSON
    return JsonResponse(response_data)

@login_required
@user_passes_test(is_global_admin)
def download_resource_logs(request):
    """Download the resource logs CSV file"""
    try:
        # Find the CSV file using the same logic as log_resource_data_to_csv
        possible_paths = [
            os.path.join(os.getcwd(), 'resource_logs.csv'),  # Current directory (tutorial/myapp)
            os.path.join(os.path.dirname(os.getcwd()), 'resource_logs.csv'),  # Parent directory (tutorial)
            os.path.join(os.path.dirname(os.path.dirname(os.getcwd())), 'resource_logs.csv'),  # Project root
        ]
        
        csv_file_path = None
        for path in possible_paths:
            if os.path.exists(path):
                csv_file_path = path
                break
        
        if csv_file_path is None or not os.path.exists(csv_file_path):
            # If no file exists, create an empty one with headers
            csv_file_path = os.path.join(os.getcwd(), 'resource_logs.csv')
            with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'timestamp', 'logged_in_users', 'fullness_percentage', 'total_gb', 'used_gb', 'free_gb',
                    'ram_total', 'ram_used', 'ram_free', 'ram_percentage', 'cpu_percentage'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
        
        # Read the file and create response
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            response = HttpResponse(csvfile.read(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="resource_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
            
        print(f"{timestamp()}Resource logs CSV downloaded by {request.user.username}")
        return response
        
    except Exception as e:
        print(f"Error downloading resource logs: {e}")
        # Return an error response
        response = HttpResponse("Error: Could not download resource logs CSV file.", content_type='text/plain')
        response.status_code = 500
        return response

# views.py
from django.contrib.auth.views import LoginView

class CustomLoginView(LoginView):
    def get_initial(self):
        initial = super().get_initial()
        username = self.request.GET.get('username')
        if username:
            initial['username'] = username
        return initial
