
import pprint
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.db import connection, DatabaseError
from django.apps import apps
import form_designer
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
from .views_helpers import is_db_admin, is_global_admin



@login_required
def home(request):
    if is_global_admin(request.user):
        return redirect('admin_overview')
    elif is_db_admin(request.user):
        return redirect('overview')  
    else:
        return redirect('user_functions')  
    

@login_required
@user_passes_test(is_db_admin)
def apollon(request):
    return render(request, 'apollon.html')
    
@login_required
def user_functions(request):
    dir = get_user_directory(request.user.username)
    sql_files = []
    if os.path.exists(dir):
        sql_files = [file[:-4] for file in os.listdir(dir) if file.endswith('.sql')]
    context = {'sqlfiles': sql_files}
    return render(request, 'user_functions.html', context)
