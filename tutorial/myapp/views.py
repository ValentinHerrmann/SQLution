
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



# Create your views here.
def home(request):
    #tables = [m._meta.db_table for c in apps.get_app_configs() for m in c.get_models()]
    #if(request.user.username == ''):
    #    loadDB('anonymous')
    #else:
    #    loadDB(request.user.username)
        
    if request.user.username.endswith('_admin'):
        return redirect('db_models')  # Replace 'db_models' with the actual URL name for /db_models/
    else:
        return redirect('user_functions')  # Replace 'user' with the actual URL name for /user/
    #return render(request, 'home.html', {'tables': None})

def apollon(request):
    return render(request, 'apollon.html')

def logged_in(request):
    print("Logged in: " + request.user.username)
    if request.user.username == 'admin':
        return redirect('admin')  # Redirect to the admin page
    loadDB(request.user.username)
    return redirect('home')  # Redirect to the home page after login


def sql_query_view(request):
    result = None
    error = None
    columns = []
    rowcount = 0

    html_output = convert_sqlite_master_to_html(request.user.username)

    if request.method == 'POST':
        form = SQLQueryForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data['query']
            try:
                cursor = runSql(query, request.user.username)

                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    result = cursor.fetchall()
                    rowcount = f"{len(result)} Zeile(n) gefunden."
                else:
                    result = ""
                    rowcount = f"{cursor.rowcount} Zeile(n) verändert."
            except Exception as e:
                rowcount = f"Keine Zeilen verändert."
                error = str(e)
            try:
                if query.strip().upper().startswith("INSERT INTO"):
                            table_name = query.split()[2]
                            select_query = f"SELECT * FROM {table_name}"
                            cursor = runSql(select_query, request.user.username)
                            if cursor is None:
                                return render(request, 'sql.html', {
                                    'form': form,
                                    'result': {},
                                    'error': 'No result found.',
                                    'columns': [],
                                    'rowcount': -1,
                                    'tablescheme': html_output,
                                })
                            columns = [col[0] for col in cursor.description]
                            result = cursor.fetchall()
            except Exception as e:
                print(str(e))
    else:
        form = SQLQueryForm()

    return render(request, 'sql.html', {
        'form': form,
        'result': result,
        'error': error,
        'columns': columns,
        'rowcount': rowcount,
        'tablescheme': html_output,
    })

def db_models(request):
    
    tables = []

    cursor = runSql("SELECT name FROM sqlite_master WHERE type='table' AND NOT name LIKE 'sqlite_%';", request.user.username)
    if(cursor is None):
        #print("No tables found.")
        return render(request, 'db_models.html', {
            'models': None
        })
    tablenames = [row[0] for row in cursor.fetchall()]

    for t in tablenames:
        cursor11 = runSql(f"SELECT * FROM {t} LIMIT 11;", request.user.username)
        cursor10 = runSql(f"SELECT * FROM {t} LIMIT 10;", request.user.username)
        
        #print(cursor10.fetchall())
        c10_result = cursor10.fetchall()
        c11_result = cursor11.fetchall()

        tables.append(
            {
                'name': t,
                'columns': [col[0] for col in cursor10.description],
                'rows': c10_result + ([['. . .' for _ in cursor10.description]] if len(c11_result) > len(c10_result) else [])
            }
        )
        #print(tables)

    return render(request, 'db_models.html', {
        'models': tables
    })

def upload_json(request):
    if request.method == 'POST' and request.FILES.get('json_file'):
        json_file = request.FILES['json_file']
        try:
            data = json.loads(json_file.read().decode('utf-8'))

            # Call your existing extract_tables function to get SQL
            sql_output = format_sql(extract_tables(data))
            binaryDB = create_db(sql_output, request.user.username)  # Call the function to execute SQL statements

            if DatabaseModel.objects.filter(user=request.user.username).exists():
                db_model = DatabaseModel.objects.get(user=request.user.username)
                db_model.json = data
                db_model.sql = sql_output
                db_model.db = binaryDB
                db_model.save()  # Update the existing entry with the new data
            else:
                DatabaseModel.objects.create(user=request.user.username,json=data, sql=sql_output, db=binaryDB, updated_at=str(datetime.now()))  # Create a new entry with the binary data
            DatabaseModel.save_base()

            #DatabaseModel.objects.filter(user=request.user.username).delete()  # Delete old entries for the user
            #DatabaseModel.objects.create(user=request.user.username,json=data, sql=sql_output, db=binaryDB)  # Create a new entry with the binary data
        except:
            return redirect('apollon')  # Redirect to home if error occurs
    return redirect('db_models')  # Redirect to home after processing
    #return render(request, 'upload_json.html', {'sqlquery': sql_output})



def index(request):
    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 0)
    num_visits += 1
    request.session['num_visits'] = num_visits

    context = {
        'num_visits': num_visits,
    }

    # Render the HTML template index.html with the data in the context variable.
    return render(request, 'index.html', context=context)

def logged_out(request):
    user = request.user.username
    if user == '':
        user = request.GET.get("user") 
    if user is not None and user != '':
        print("Logged out: " + user)
        storeDB(user)
    logout(request)  # Log out the user
    request.session.flush()  # Clear the session data
    return redirect('/accounts/login')  # Redirect to the login page

def download_db(request):
    try:
        db_file = open(get_db_name(request.user.username), "rb").read()
        response = HttpResponse(db_file, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="datenbank_{datetime.now().strftime("%Y-%m-%d_%H-%M")}.db"'
        return response
    except DatabaseModel.DoesNotExist:
        return redirect('db_models')  # Redirect if no database exists for the user
    return redirect('db_models')

def upload_db(request):
    #print("Upload DB")
    if request.method == "POST" and request.FILES.get('db_file'):
        db_file = request.FILES['db_file']
        with open(get_db_name(request.user.username), "wb+") as destination:
            for chunk in db_file.chunks():
                destination.write(chunk)
    return redirect('db_models')