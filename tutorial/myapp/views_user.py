
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

def timestamp():
    return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]") + "\t"

@login_required
def logged_in(request):
    user = request.user.username
    print(timestamp() + "Logged in: " + user)
    if user == 'admin':
        return redirect('/admin')  # Redirect to the admin page
    restore_zip_to_directory(get_user_directory(user))
    return redirect('home')  # Redirect to the home page after login


def logged_out(request):
    user = request.user.username
    if user == '':
        user = request.GET.get("user") 
    if user is not None and user != '':
        print(timestamp() + "Logged out: " + user)
        zip_and_save_directory(get_user_directory(user))
    logout(request)  # Log out the user
    request.session.flush()  # Clear the session data
    return redirect('/accounts/login')  # Redirect to the login page