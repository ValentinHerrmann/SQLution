import json
from django.http import HttpResponse, JsonResponse
import psutil
from myapp.utils.decorators import *
from django.contrib.auth.decorators import login_required,user_passes_test
from myapp.utils.directories import *
from myapp.utils.diagram import load_json
from myapp.utils.utils import *
from myapp.utils.users import *

# Import functions from views_user.py
from .. import views_user

@login_required
@user_passes_test(is_db_admin)
def api_sql(request, filename:str):
    try:
        filename = filename.replace('.sql.sql', '.sql')

        if(not filename.endswith('.sql')):
            filename += '.sql'

        dir = get_user_directory(request.user.username)


        if(request.method == "POST"):

            body_unicode = request.body.decode('utf-8')
            body = json.loads(body_unicode)
            sql = body['sql']

            with open(fullpath(dir,f"{filename}"), 'w') as f:
                f.write(sql)
            sqllock_release(dir)
            return HttpResponse("File saved successfully", status=200)

        if(request.method == "GET"):
            with open(fullpath(dir,f"{filename}"), 'r') as f:
                file_content = f.read()
                sqllock_release(dir)
                return HttpResponse(file_content, content_type="text/sql")
        
        if(request.method == "DELETE"):
            if os.path.exists(fullpath(dir,f"{filename}")):
                os.remove(fullpath(dir,f"{filename}"))
                sqllock_release(dir)
                return HttpResponse("File deleted successfully", status=200)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sqllock_release(dir)
        return HttpResponse("Unknown request", status=500)

@login_required
@user_passes_test(is_db_admin)
def api_sql_all(request):
    try:
        dir = get_user_directory(request.user.username)
        sqllock_get(dir)

        if(request.method == "POST"):

            # delete all files in folder dir
            for file in os.listdir(dir):
                if file.endswith('.sql'):
                    os.remove(os.path.join(dir, file))

            body_unicode = request.body.decode('utf-8')
            body = json.loads(body_unicode)
            files = body['files']


            for file in files:
                filename = file['filename']
                sql = file['sql']

                filename = filename.replace('.sql.sql', '.sql')
                if(not filename.endswith('.sql')):
                    filename += '.sql'
                dir = get_user_directory(request.user.username)

                with open(fullpath(dir,f"{filename}"), 'w') as f:
                    f.write(sql)

            sqllock_release(dir)
            return HttpResponse("Files saved successfully", status=200)
        
        return HttpResponse("Unknown request", status=404)
    except Exception as e:
        print(f"Error: {e}")
        return HttpResponse("Internal Error", status=500)
    finally:
        sqllock_release(dir)

@login_required
@user_passes_test(is_db_admin)
def api_upload_db(request):
    try:
        dir = get_user_directory(request.user.username)
        file_path = os.path.join(dir, "datenbank.db")

        if(request.method == "POST"):                
            with open(file_path, 'wb+') as destination:
                destination.write(request.body)
            return HttpResponse("File saved successfully", status=201)
    except Exception as e:
        print(f"Error: {e}")
    return HttpResponse("Internal Error", status=500)

@login_required
@user_passes_test(is_db_admin)
def api_diagram_json(request):
    dir = get_user_directory(request.user.username)
    try:
        sqllock_get(dir)
        print(request.method)
        if(request.method == "GET"):
            with open(f'{dir}/model.json', 'rb') as f:
                file_content = f.read()
            return HttpResponse(file_content, content_type="application/json")
        elif(request.method == "POST"):
            load_json(request.body,request.user.username)
            return HttpResponse("", status=200)
        else:
            return HttpResponse("", status=405)

            
    except Exception as e:
        print(f"Error: {e}")
        return HttpResponse("Internal Error", status=500)
    finally:
        sqllock_release(dir)

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
    total_gb = round(total /(1024 ** 3), 2)
    used_gb = round(used / (1024 ** 3), 2)
    free_gb = round(free / (1024 ** 3), 2)

    # Get RAM usage
    try:
        ram = psutil.virtual_memory()
        ram_total = round(ram.total / (1024 ** 3), 2)
        ram_used = round(ram.used / (1024 ** 3), 2)
        ram_free = round(ram.available / (1024 ** 3), 2)
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

    # Get detailed session information
    session_details = get_session_details()
    print(session_details)
    
    # Get recent audit logs
    recent_audit_logs = views_user.get_recent_audit_logs()
    
    # Prepare response data
    response_data = {
        'directories': user_data,
        "fullness_percentage": int(round(fullness_percentage, 0)),
        "total_gb": "{:.2f}".format(total_gb),
        "used_gb": "{:.2f}".format(used_gb),
        "free_gb": "{:.2f}".format(free_gb),
        "ram_total": "{:.2f}".format(ram_total),
        "ram_used": "{:.2f}".format(ram_used),
        "ram_free": "{:.2f}".format(ram_free),
        "ram_percentage": int(round(ram_percentage, 0)),
        "cpu_percentage": int(round(cpu_percentage, 0)),
        "logged_in_users": logged_in_users,
        "session_info": session_details,
        "recent_audit_logs": [
            {
                'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'username': log.username,
                'action': log.action,
                'action_display': dict(log.ACTION_CHOICES).get(log.action, log.action),
                'ip_address': log.ip_address or 'Unknown',
                'operating_system': log.operating_system or 'Unknown',
                'location': log.location or 'Unknown',
                'session_id': log.session_id or 'Unknown'
            } for log in recent_audit_logs
        ]
    }

    # Log data to CSV
    print(f"{timestamp()}Attempting to log resource data to CSV...")
    views_user.log_resource_data_to_csv(response_data)
    print(f"{timestamp()}CSV logging completed.")
    
    # Check for audit log rotation (every 10th call to avoid overhead)
    import random
    if random.randint(1, 10) == 1:  # Run rotation check roughly 10% of the time
        try:
            print(f"{timestamp()}Checking audit log rotation...")
            views_user.rotate_audit_logs()
        except Exception as e:
            print(f"{timestamp()}Error during audit log rotation check: {e}")

    # Return data as JSON
    return JsonResponse(response_data)
