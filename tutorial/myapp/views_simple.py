
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
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib.auth import logout
import os
import re


def home(request):
    if request.user.username.endswith('_admin'):
        return redirect('db_models')  
    else:
        return redirect('user_functions')  
    
@login_required
def apollon(request):
    return render(request, 'apollon.html')
    
@login_required
def user_functions(request):
    username = request.user.username
    if username.endswith('_admin'):
        username = username[:-6]
    directory = f"user_databases/{username}/"
    sql_files = []
    if os.path.exists(directory):
        sql_files = [file[:-4] for file in os.listdir(directory) if file.endswith('.sql')]
    context = {'sqlfiles': sql_files}
    return render(request, 'user_functions.html', context)
