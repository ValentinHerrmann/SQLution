

import csv
from django.utils import timezone
from myapp.utils.utils import *
from django.contrib.sessions.models import Session

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

def get_logged_in_users_count():
    """Get the number of currently logged in users - now with working logic"""
    try:
        from django.contrib.auth.models import User
        from datetime import timedelta
        
        # Get current time
        current_time = timezone.now()
        
        # More aggressive session cleanup - remove expired sessions immediately
        try:
            expired_sessions = Session.objects.filter(expire_date__lt=current_time)
            expired_count = expired_sessions.count()
            if expired_count > 0:
                expired_sessions.delete()
                print(f"{timestamp()}Cleaned up {expired_count} expired sessions")
        except Exception as e:
            print(f"Session cleanup failed: {e}")
        
        # Also clean up sessions that are older than session security timeout
        try:
            # Sessions older than session security timeout should be considered invalid
            security_cutoff = current_time - timedelta(seconds=3600)  # 1 hour cutoff
            old_sessions = Session.objects.filter(expire_date__lt=security_cutoff)
            old_count = old_sessions.count()
            if old_count > 0:
                old_sessions.delete()
                print(f"{timestamp()}Cleaned up {old_count} old sessions beyond security timeout")
        except Exception as e:
            print(f"Old session cleanup failed: {e}")
        
        # Get all sessions that haven't expired yet
        active_sessions = Session.objects.filter(expire_date__gte=current_time)
        
        # Count unique logged-in users from active sessions
        logged_in_user_ids = set()
        valid_sessions = 0
        invalid_sessions = 0
        
        for session in active_sessions:
            try:
                session_data = session.get_decoded()
                user_id = session_data.get('_auth_user_id')
                
                # Only count if there's actually a user ID
                if user_id:
                    try:
                        # Verify the user exists and is active
                        user = User.objects.get(id=user_id, is_active=True)
                        
                        # Additional check: if session_security is being used, check last activity
                        session_security_data = session_data.get('session_security')
                        if session_security_data and isinstance(session_security_data, dict):
                            # If there's session security data, be more strict about timing
                            last_activity = session_security_data.get('last_activity')
                            if last_activity:
                                try:
                                    last_activity_time = timezone.datetime.fromtimestamp(
                                        last_activity, tz=timezone.get_current_timezone()
                                    )
                                    # Check if last activity was within reasonable time (1 hour)
                                    if (current_time - last_activity_time).total_seconds() > 3600:
                                        print(f"{timestamp()}Session for user {user_id} too old, skipping")
                                        continue
                                except Exception:
                                    pass  # If we can't parse last activity, continue with basic check
                        
                        logged_in_user_ids.add(user_id)
                        valid_sessions += 1
                    except User.DoesNotExist:
                        invalid_sessions += 1
                        continue
                        
            except Exception:
                # Skip sessions that can't be decoded
                invalid_sessions += 1
                continue
        
        user_count = len(logged_in_user_ids)
        total_users = User.objects.filter(is_active=True).count()
        
        print(f"{timestamp()}Active sessions: {active_sessions.count()}")
        print(f"{timestamp()}Valid sessions with users: {valid_sessions}")
        print(f"{timestamp()}Invalid/skipped sessions: {invalid_sessions}")
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
            for session in active_sessions[:3]:  # Check first 3 sessions
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
