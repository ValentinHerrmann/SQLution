
import pprint
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.db import connection, DatabaseError
from django.apps import apps
import form_designer
import shutil

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
    
    def get_directory_tree_with_sizes(directory):
        tree = []
        for root, dirs, files in os.walk(directory):
            for name in dirs:
                dir_path = os.path.join(root, name)
                size = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, _, filenames in os.walk(dir_path)
                    for filename in filenames
                )
                sizeK = round(size / 1000, 2)
                sizeM = round(size / (1000*1000), 3)
                tree.append({'type': 'directory', 'name': name, 'size':  sizeK})
            #for name in files:
            #    file_path = os.path.join(root, name)
            #    size = os.path.getsize(file_path)
            #    tree.append({'type': 'file', 'name': file_path, 'size': size})
        return tree

    user_databases_path = os.path.join(os.getcwd(), 'user_databases')
    user_data = get_directory_tree_with_sizes(user_databases_path)


    # Get system drive usage
    total, used, free = shutil.disk_usage("/")
    fullness_percentage = (used / total) * 100

    # Convert absolute values to GB for readability
    total_gb = round(total / (1000 ** 3), 2)
    used_gb = round(used / (1000 ** 3), 2)
    free_gb = round(free / (1000 ** 3), 2)

    return render(request, 'admin_overview.html', {
        'users': user_data,
        "fullness_percentage": round(fullness_percentage, 2),  # Round to 2 decimal places
        "total_gb": total_gb,
        "used_gb": used_gb,
        "free_gb": free_gb,
    })