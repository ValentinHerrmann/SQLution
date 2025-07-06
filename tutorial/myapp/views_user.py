
import pprint
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.db import connection, DatabaseError
from django.apps import apps
import form_designer
import shutil
import psutil


from .views_helpers import is_global_admin

from .forms import SQLQueryForm,UploadFileForm
from .models import *
from .utils import *  # Assuming you have this function in utils.py
from .sqlite_connector import *  # Import sqlite3 for SQLite database connection
import json
from datetime import datetime
from django.contrib.auth.decorators import login_required, user_passes_test

from django.shortcuts import redirect
from django.contrib.auth import logout
import os
import re

def timestamp():
    return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]") + "\t"

@login_required
def logged_in(request):
    user = request.user.username
    print(timestamp() + "Logged in: " + user)
    if user == 'admin':
        pass#return redirect('admin')  # Redirect to the admin page
    #restore_zip_to_directory(get_user_directory(user))
    return redirect('home')  # Redirect to the home page after login


def logged_out(request):
    user = request.user.username
    if user == '':
        user = request.GET.get("user") 
    if user is not None and user != '':
        print(timestamp() + "Logged out: " + user)
        #zip_and_save_directory(get_user_directory(user))
    logout(request)  # Log out the user
    request.session.flush()  # Clear the session data
    return redirect('/accounts/login')  # Redirect to the login page+
    

@login_required
@user_passes_test(is_global_admin)
def admin_overview(request):  
    restart = request.GET.get("restart")
    if restart == 'true':
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

    user_databases_path = os.path.join(os.getcwd(), 'user_databases')
    user_data = get_directory_tree_with_sizes(user_databases_path)

    # Get system drive usage
    total, used, free = shutil.disk_usage("/")
    fullness_percentage = (used / total) * 100

    # Convert absolute values to GB for readability
    total_gb = round(total / (1000 ** 3), 2)
    used_gb = round(used / (1000 ** 3), 2)
    free_gb = round(free / (1000 ** 3), 2)

    # Get RAM usage
    ram = psutil.virtual_memory()
    ram_total = round(ram.total / (1000 ** 3), 2)
    ram_used = round(ram.used / (1000 ** 3), 2)
    ram_free = round(ram.available / (1000 ** 3), 2)
    ram_percentage = ram.percent

    # Get CPU usage
    #val = os.getenv('RESOURCES_REFRESH', default=5000)/1000
    cpu_percentage = psutil.cpu_percent(0.5)

    # Return data as JSON
    return JsonResponse({
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
    })

# views.py
from django.contrib.auth.views import LoginView

class CustomLoginView(LoginView):
    def get_initial(self):
        initial = super().get_initial()
        username = self.request.GET.get('username')
        if username:
            initial['username'] = username
        return initial
