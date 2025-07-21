
from django.http import HttpResponse
from django.shortcuts import redirect
from myapp.models import *
from myapp.utils.utils import *  
from myapp.utils.sqlite_connector import * 
from datetime import datetime
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect

import zipfile

from myapp.utils.decorators import *
from myapp.utils.diagram import *
from myapp.utils.directories import *


@user_passes_test(is_db_admin)
@login_required
def download_db(request):
    try:
        db_file = open(get_db_name(request.user.username), "rb").read()
        response = HttpResponse(db_file, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="datenbank_{datetime.now().strftime("%Y-%m-%d_%H-%M")}.db"'
        return response
    except Exception as e:
        return redirect('overview')  # Redirect if no database exists for the user

@login_required
@user_passes_test(is_db_admin)
def upload_db(request):
    if request.method == "POST" and request.FILES.get('db_file'):
        db_file = request.FILES['db_file']
        with open(get_db_name(request.user.username), "wb+") as destination:
            for chunk in db_file.chunks():
                destination.write(chunk)
    return redirect('overview')



@login_required
@user_passes_test(is_db_admin)
def upload_json(request):
    if request.method == 'POST' and request.FILES.get('json_file'):
        json_file = request.FILES['json_file']
        load_json(json_file, request.user.username)
    return redirect('apollon')

@login_required
@user_passes_test(is_db_admin)
def download_zip(request):
    try:
        zip_file = zip_and_save_directory(get_user_directory(request.user.username), False)
        response = HttpResponse(zip_file, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="datenbank_{request.user.username[:-6]}{datetime.now().strftime("%Y-%m-%d")}.zip"'
        return response
    except Exception as e:
        return redirect('overview')
    

@login_required
@user_passes_test(is_db_admin)
def upload_zip(request):
    #print("Upload DB")
    if request.method == "POST" and request.FILES.get('zip_file'):
        zip_file = request.FILES['zip_file']
        dir = get_user_directory(request.user.username)

        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(dir)
    return redirect('overview')

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



        