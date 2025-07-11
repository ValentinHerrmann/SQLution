
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

def load_json(json_bytes, username):
    try:
        json_string = json_bytes.decode('utf-8')
        data = json.loads(json_string)
        
        sql_output = format_sql(extract_tables(data))

        with open(get_user_directory(username)+'/_CreateDB.sql_', "w") as f:
            f.write(sql_output)
        with open(get_user_directory(username)+'/model.json', "wb+") as f:
            f.write(json_bytes)
        create_db(sql_output, username)  # Call the function to execute SQL statements

    except Exception as e:
        print(f"Error: {e}")


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