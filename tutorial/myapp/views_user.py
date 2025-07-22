
import pprint
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.db import connection, DatabaseError
from django.apps import apps
from django.contrib import messages
import form_designer
import shutil
import psutil
import csv
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.utils import timezone

from myapp.utils.decorators import *
from myapp.utils.users import *

from myapp.views.forms import SQLQueryForm,UploadFileForm
from myapp.models import *
from myapp.utils.utils import *  # Assuming you have this function in utils.py
from myapp.utils.sqlite_connector import *  # Import sqlite3 for SQLite database connection
from myapp.utils.directories import get_directory_tree_with_sizes
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


def log_resource_data_to_csv(data):
    """Log resource data to CSV file with semicolon separator and comma decimal separator"""
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
        
        # Check if log rotation is needed before writing
        rotate_log_file(csv_file_path)
        
        file_exists = os.path.isfile(csv_file_path)
        
        def format_number(value):
            """Format number with comma as decimal separator"""
            if isinstance(value, (int, float)):
                return str(value).replace('.', ',')
            elif isinstance(value, str):
                # Handle string values that might already be formatted with decimal points
                return value.replace('.', ',')
            return str(value)
        
        with open(csv_file_path, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'timestamp', 'logged_in_users', 'fullness_percentage', 'total_gb', 'used_gb', 'free_gb',
                'ram_total', 'ram_used', 'ram_free', 'ram_percentage', 'cpu_percentage'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            
            # Write header if file is new
            if not file_exists:
                writer.writeheader()
            
            # Write the data with formatted numbers
            csv_data = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'logged_in_users': format_number(data.get('logged_in_users', 0)),
                'fullness_percentage': format_number(data.get('fullness_percentage', 0)),
                'total_gb': format_number(data.get('total_gb', 0)),
                'used_gb': format_number(data.get('used_gb', 0)),
                'free_gb': format_number(data.get('free_gb', 0)),
                'ram_total': format_number(data.get('ram_total', 0)),
                'ram_used': format_number(data.get('ram_used', 0)),
                'ram_free': format_number(data.get('ram_free', 0)),
                'ram_percentage': format_number(data.get('ram_percentage', 0)),
                'cpu_percentage': format_number(data.get('cpu_percentage', 0))
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
    
    # Get the session key before logout to ensure it gets cleaned up
    session_key = request.session.session_key
    
    if request.user.is_authenticated:
        logout(request)  # Log out the user
    
    # Clean up the session thoroughly
    request.session.flush()  # Clear the session data
    
    # Additional cleanup: try to remove the session from database immediately
    if session_key:
        try:
            Session.objects.filter(session_key=session_key).delete()
            print(f"{timestamp()}Cleaned up session {session_key} for user {user}")
        except Exception as e:
            print(f"{timestamp()}Error cleaning up session: {e}")
    
    # Clear any relevant cache entries that might affect user counting
    try:
        from django.core.cache import cache
        cache.clear()
        print(f"{timestamp()}Cleared Django cache to ensure fresh user counts")
    except Exception as e:
        print(f"{timestamp()}Cache clear failed: {e}")
    
    # Force a cleanup of expired sessions to ensure count accuracy
    try:
        from django.utils import timezone
        current_time = timezone.now()
        expired_count = Session.objects.filter(expire_date__lt=current_time).delete()[0]
        if expired_count > 0:
            print(f"{timestamp()}Post-logout cleanup: removed {expired_count} expired sessions")
    except Exception as e:
        print(f"{timestamp()}Post-logout session cleanup failed: {e}")
    
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
        'refresh_rate': settings.RESOURCES_REFRESH,
        'commit': os.popen('git log -1 --pretty=%B').read().strip(),
        'last_launched': last_launched,
        'wdir': os.getcwd(),
        'logged_in_users': get_logged_in_users_count(),  # Add initial logged-in users count
        'session_info': get_session_details(),  # Add initial session details
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
def download_resource_logs(request):
    """Download the resource logs CSV file with semicolon separator"""
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
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
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

@user_passes_test(lambda u: u.is_staff)
def download_audit_logs(request):
    """Download audit logs as CSV file with semicolon separator"""
    try:
        from myapp.models import AuditLog
        
        # Create HTTP response with CSV content type
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="audit_logs_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        # Create CSV writer with semicolon delimiter
        writer = csv.writer(response, delimiter=';')
        
        # Write header row
        writer.writerow([
            'Timestamp',
            'Username', 
            'Action',
            'IP Address',
            'Operating System',
            'Location',
            'Forced Reason',
            'Session ID'
        ])
        
        # Get all audit logs ordered by timestamp (newest first)
        audit_logs = AuditLog.objects.all().order_by('-timestamp')
        
        # Write data rows
        for log in audit_logs:
            writer.writerow([
                log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                log.username,
                dict(AuditLog.ACTION_CHOICES).get(log.action, log.action),
                log.ip_address or 'Unknown',
                log.operating_system or 'Unknown',
                log.location or 'Unknown',
                log.forced_reason or '',
                log.session_id or ''
            ])
        
        return response
        
    except Exception as e:
        print(f"Error downloading audit logs: {e}")
        response = HttpResponse("Error: Could not download audit logs CSV file.", content_type='text/plain')
        response.status_code = 500
        return response

from django.contrib.auth.views import LoginView
from django.conf import settings
import glob

class CustomLoginView(LoginView):
    def get_initial(self):
        initial = super().get_initial()
        username = self.request.GET.get('username')
        if username:
            initial['username'] = username
        return initial

def rotate_log_file(file_path, max_size_mb=None, max_files=None):
    """
    Rotate log file if it exceeds the maximum size.
    Archive old files with timestamp and keep only max_files number of archives.
    """
    try:
        if max_size_mb is None:
            max_size_mb = getattr(settings, 'LOG_ROTATION_MAX_SIZE_MB', 10)
        if max_files is None:
            max_files = getattr(settings, 'LOG_ROTATION_MAX_FILES', 4)
        
        if not os.path.exists(file_path):
            return False
        
        # Check file size
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        
        if file_size_mb >= max_size_mb:
            # Create timestamp for archive
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create archive filename
            file_dir = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            name_parts = os.path.splitext(file_name)
            archive_path = os.path.join(file_dir, f"{name_parts[0]}_{timestamp_str}{name_parts[1]}")
            
            # Move current file to archive
            shutil.move(file_path, archive_path)
            print(f"{timestamp()}Rotated log file: {file_path} -> {archive_path}")
            
            # Clean up old archives (keep only max_files)
            pattern = os.path.join(file_dir, f"{name_parts[0]}_*{name_parts[1]}")
            archive_files = sorted(glob.glob(pattern), key=os.path.getctime, reverse=True)
            
            # Remove excess files
            for old_file in archive_files[max_files:]:
                try:
                    os.remove(old_file)
                    print(f"{timestamp()}Removed old archive: {old_file}")
                except Exception as e:
                    print(f"{timestamp()}Error removing old archive {old_file}: {e}")
            
            return True
    
    except Exception as e:
        print(f"{timestamp()}Error during log rotation: {e}")
        return False
    
    return False

def get_log_rotation_info(file_path):
    """
    Get information about log rotation for a file.
    Returns the timestamp of the latest rotation or creation time.
    """
    try:
        if not os.path.exists(file_path):
            return "No file found"
        
        # Get file directory and name parts
        file_dir = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        name_parts = os.path.splitext(file_name)
        
        # Look for archive files
        pattern = os.path.join(file_dir, f"{name_parts[0]}_*{name_parts[1]}")
        archive_files = glob.glob(pattern)
        
        if archive_files:
            # Find the most recent archive (latest rotation)
            latest_archive = max(archive_files, key=os.path.getctime)
            archive_name = os.path.basename(latest_archive)
            
            # Extract timestamp from archive filename
            try:
                timestamp_part = archive_name.replace(name_parts[0] + "_", "").replace(name_parts[1], "")
                rotation_time = datetime.strptime(timestamp_part, "%Y%m%d_%H%M%S")
                return f"Last rotated: {rotation_time.strftime('%Y-%m-%d %H:%M:%S')}"
            except:
                return f"Last rotated: {datetime.fromtimestamp(os.path.getctime(latest_archive)).strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            # No archives, show current file creation time
            creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
            return f"Created: {creation_time.strftime('%Y-%m-%d %H:%M:%S')}"
    
    except Exception as e:
        return f"Error: {str(e)}"

def get_file_size_formatted(file_path):
    """Get file size in a human-readable format"""
    try:
        if os.path.exists(file_path):
            size_bytes = os.path.getsize(file_path)
            if size_bytes == 0:
                return "0 B"
            
            size_names = ["B", "KB", "MB", "GB", "TB"]
            import math
            i = int(math.floor(math.log(size_bytes, 1024)))
            p = math.pow(1024, i)
            s = round(size_bytes / p, 2)
            return f"{s} {size_names[i]}"
        else:
            return "File not found"
    except Exception as e:
        return f"Error: {str(e)}"

def get_resource_log_file_size():
    """Get rotation information for the resource logs CSV file"""
    try:
        # Find the CSV file using the same logic as log_resource_data_to_csv
        possible_paths = [
            os.path.join(os.getcwd(), 'resource_logs.csv'),  # Current directory (tutorial/myapp)
            os.path.join(os.path.dirname(os.getcwd()), 'resource_logs.csv'),  # Parent directory (tutorial)
            os.path.join(os.path.dirname(os.path.dirname(os.getcwd())), 'resource_logs.csv'),  # Project root
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return get_log_rotation_info(path)
        
        return "No file found"
    except Exception as e:
        return f"Error: {str(e)}"

def rotate_audit_logs():
    """
    Rotate audit logs if they exceed the maximum count.
    Archive old logs to CSV files and clean up database.
    """
    try:
        from myapp.models import AuditLog
        max_records = getattr(settings, 'LOG_ROTATION_MAX_SIZE_MB', 10) * 1000  # Convert MB to approximate record count
        max_files = getattr(settings, 'LOG_ROTATION_MAX_FILES', 4)
        
        total_count = AuditLog.objects.count()
        
        if total_count >= max_records:
            # Create archive CSV file
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Find appropriate directory for audit archives
            possible_paths = [
                os.path.join(os.getcwd(), f'audit_logs_{timestamp_str}.csv'),
                os.path.join(os.path.dirname(os.getcwd()), f'audit_logs_{timestamp_str}.csv'),
                os.path.join(os.path.dirname(os.path.dirname(os.getcwd())), f'audit_logs_{timestamp_str}.csv'),
            ]
            
            archive_path = None
            for path in possible_paths:
                try:
                    test_dir = os.path.dirname(path)
                    if os.path.exists(test_dir) and os.access(test_dir, os.W_OK):
                        archive_path = path
                        break
                except:
                    continue
            
            if archive_path is None:
                archive_path = os.path.join(os.getcwd(), f'audit_logs_{timestamp_str}.csv')
            
            # Get logs to archive (keep newest 1000, archive the rest)
            keep_count = 1000
            logs_to_archive = AuditLog.objects.order_by('timestamp')[:-keep_count]
            
            if logs_to_archive.exists():
                # Create CSV archive
                with open(archive_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile, delimiter=';')
                    
                    # Write header
                    writer.writerow([
                        'Timestamp', 'Username', 'Action', 'IP Address', 
                        'Operating System', 'Location', 'Forced Reason', 'Session ID'
                    ])
                    
                    # Write archived logs
                    for log in logs_to_archive:
                        writer.writerow([
                            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                            log.username,
                            dict(AuditLog.ACTION_CHOICES).get(log.action, log.action),
                            log.ip_address or 'Unknown',
                            log.operating_system or 'Unknown',
                            log.location or 'Unknown',
                            log.forced_reason or '',
                            log.session_id or ''
                        ])
                
                # Delete archived logs from database
                archived_count = logs_to_archive.count()
                logs_to_archive.delete()
                
                print(f"{timestamp()}Archived {archived_count} audit logs to: {archive_path}")
                
                # Clean up old archive files
                archive_dir = os.path.dirname(archive_path)
                pattern = os.path.join(archive_dir, 'audit_logs_*.csv')
                archive_files = sorted(glob.glob(pattern), key=os.path.getctime, reverse=True)
                
                for old_file in archive_files[max_files:]:
                    try:
                        os.remove(old_file)
                        print(f"{timestamp()}Removed old audit archive: {old_file}")
                    except Exception as e:
                        print(f"{timestamp()}Error removing old audit archive {old_file}: {e}")
                
                return True
        
        return False
    
    except Exception as e:
        print(f"{timestamp()}Error during audit log rotation: {e}")
        return False

def get_audit_rotation_info():
    """Get information about audit log rotation"""
    try:
        # Look for archive files
        possible_dirs = [
            os.getcwd(),
            os.path.dirname(os.getcwd()),
            os.path.dirname(os.path.dirname(os.getcwd())),
        ]
        
        latest_archive = None
        for directory in possible_dirs:
            pattern = os.path.join(directory, 'audit_logs_*.csv')
            archive_files = glob.glob(pattern)
            if archive_files:
                dir_latest = max(archive_files, key=os.path.getctime)
                if latest_archive is None or os.path.getctime(dir_latest) > os.path.getctime(latest_archive):
                    latest_archive = dir_latest
        
        if latest_archive:
            archive_name = os.path.basename(latest_archive)
            try:
                timestamp_part = archive_name.replace('audit_logs_', '').replace('.csv', '')
                rotation_time = datetime.strptime(timestamp_part, "%Y%m%d_%H%M%S")
                return f"Last archived: {rotation_time.strftime('%Y-%m-%d %H:%M:%S')}"
            except:
                return f"Last archived: {datetime.fromtimestamp(os.path.getctime(latest_archive)).strftime('%Y-%m-%d %H:%M:%S')}"
        
        # No archives found, check database age
        from myapp.models import AuditLog
        oldest = AuditLog.objects.order_by('timestamp').first()
        if oldest:
            return f"Database since: {oldest.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            return "No audit logs"
    
    except Exception as e:
        return f"Error: {str(e)}"

def get_audit_log_count():
    """Get rotation information for audit logs (wrapper for compatibility)"""
    return get_audit_rotation_info()

def get_recent_audit_logs(limit=20):
    """Get recent audit logs for display in admin overview"""
    try:
        from myapp.models import AuditLog
        return AuditLog.objects.all().order_by('-timestamp')[:limit]
    except Exception as e:
        print(f"Error getting recent audit logs: {e}")
        return []

@login_required
@user_passes_test(is_global_admin)
def clear_resource_logs(request):
    """Clear the resource logs CSV file"""
    if request.method == 'POST':
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
            
            if csv_file_path and os.path.exists(csv_file_path):
                # Clear the file by recreating it with just headers
                with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = [
                        'timestamp', 'logged_in_users', 'fullness_percentage', 'total_gb', 'used_gb', 'free_gb',
                        'ram_total', 'ram_used', 'ram_free', 'ram_percentage', 'cpu_percentage'
                    ]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
                    writer.writeheader()
                
                print(f"{timestamp()}Resource logs cleared by {request.user.username}")
                messages.success(request, "Performance logs have been cleared successfully.")
            else:
                messages.warning(request, "No performance logs file found to clear.")
                
        except Exception as e:
            print(f"{timestamp()}Error clearing resource logs: {str(e)}")
            messages.error(request, f"Error clearing performance logs: {str(e)}")
    
    return redirect('admin_overview')

@login_required
@user_passes_test(is_global_admin)
def clear_audit_logs(request):
    """Clear all audit logs from the database"""
    if request.method == 'POST':
        try:
            from myapp.models import AuditLog
            
            # Count existing logs
            log_count = AuditLog.objects.count()
            
            # Delete all audit logs
            AuditLog.objects.all().delete()
            
            print(f"{timestamp()}Audit logs cleared by {request.user.username} - {log_count} records deleted")
            messages.success(request, f"Audit logs have been cleared successfully. {log_count} records were deleted.")
                
        except Exception as e:
            print(f"{timestamp()}Error clearing audit logs: {str(e)}")
            messages.error(request, f"Error clearing audit logs: {str(e)}")
    
    return redirect('admin_overview')
