
from django.http import HttpResponse
from django.shortcuts import redirect
from .models import *
from .utils import *  # Assuming you have this function in utils.py
from .sqlite_connector import *  # Import sqlite3 for SQLite database connection
import json
from datetime import datetime
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect
from .views_helpers import is_db_admin
import zipfile
from django.contrib.auth import logout
import os


@user_passes_test(is_db_admin)
@login_required
def download_db(request):
    try:
        db_file = open(get_db_name(request.user.username), "rb").read()
        response = HttpResponse(db_file, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="datenbank_{datetime.now().strftime("%Y-%m-%d_%H-%M")}.db"'
        return response
    except Exception as e:
        return redirect('db_models')  # Redirect if no database exists for the user

@login_required
@user_passes_test(is_db_admin)
def upload_db(request):
    #print("Upload DB")
    if request.method == "POST" and request.FILES.get('db_file'):
        db_file = request.FILES['db_file']
        with open(get_db_name(request.user.username), "wb+") as destination:
            for chunk in db_file.chunks():
                destination.write(chunk)
    return redirect('db_models')

@login_required
@user_passes_test(is_db_admin)
def upload_json(request):
    if request.method == 'POST' and request.FILES.get('json_file'):
        json_file = request.FILES['json_file']
        try:
            json_string = json_file.read().decode('utf-8')
            data = json.loads(json_string)
            sql_output = format_sql(extract_tables(data))

            with open(get_user_directory(request.user.username)+'/CreateDB.sql', "w") as f:
                f.write(sql_output)
            with open(get_user_directory(request.user.username)+'/Model.json', "w") as f:
                f.write(json_string)
            create_db(sql_output, request.user.username)  # Call the function to execute SQL statements

        except Exception as e:
            print(f"Error: {e}")
            return redirect('apollon')  # Redirect to home if error occurs
    return redirect('db_models')  # Redirect to home after processing

@login_required
@user_passes_test(is_db_admin)
def download_zip(request):
    try:
        zip_file = zip_and_save_directory(get_user_directory(request.user.username), False)
        response = HttpResponse(zip_file, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="datenbank_{request.user.username[:-6]}{datetime.now().strftime("%Y-%m-%d")}.zip"'
        return response
    except Exception as e:
        return redirect('db_models')
    

@login_required
@user_passes_test(is_db_admin)
def upload_zip(request):
    #print("Upload DB")
    if request.method == "POST" and request.FILES.get('zip_file'):
        zip_file = request.FILES['zip_file']
        dir = get_user_directory(request.user.username)

        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(dir)
    return redirect('db_models')

@login_required
@user_passes_test(is_db_admin)
def read_file(request, username):
    if(username != request.user.username):
        print("passt net...")
    #    logout(request)
    #    request.session.flush()
    #    redirect('/accounts/login')
    dir = get_user_directory(request.user.username)
    print(request.user.username + " - " + dir)
    f = open(f'{dir}/datenbank.db', 'rb')
    file_content = f.read()
    f.close()
    return HttpResponse(file_content, content_type="application/x-sqlite3")
@login_required
@user_passes_test(is_db_admin)
def read_file_sql(request):
    dir = get_user_directory(request.user.username)
    f = open(f'{dir}/Dachau.sql', 'r')
    file_content = f.read()
    f.close()
    return HttpResponse(file_content)
