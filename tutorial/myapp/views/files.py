
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
from myapp.utils import query_access, api_utils
from django.contrib import messages


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
    print("Upload DB")
    print(request.FILES)
    if request.method == "POST" and request.FILES.get('db_file'):
        db_file = request.FILES['db_file']
        try:
            api_utils.save_database_file(get_user_directory(request.user.username), db_file.read())
        except ValueError:
            messages.error(request, 'Die Datei ist keine SQLite-Datenbank und wurde nicht hochgeladen.')
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
        try:
            query_access.import_zip(dir, zip_file)
        except zipfile.BadZipFile:
            messages.error(request, 'Die Datei ist keine gültige ZIP-Datei.')
        except ValueError:
            messages.error(request, 'Die ZIP-Datei enthält ungültige Pfade und wurde nicht importiert.')
        except TimeoutError:
            messages.error(request, 'Der Server ist gerade beschäftigt. Bitte versuche es gleich noch einmal.')
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



        