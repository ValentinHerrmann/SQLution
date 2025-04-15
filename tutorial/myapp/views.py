
import pprint
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.db import connection, DatabaseError
from django.apps import apps
import form_designer
from .forms import SQLQueryForm
from .models import *
from .utils import *  # Assuming you have this function in utils.py
from .sqlite_connector import *  # Import sqlite3 for SQLite database connection
import json


# Create your views here.
def home(request):
    tables = [m._meta.db_table for c in apps.get_app_configs() for m in c.get_models()]
    return render(request, 'home.html', {'tables': tables})

def todos(request):
    items = TodoItem.objects.all()
    return render(request, 'todos.html', {'todos': items})

def apollon(request):
    return render(request, 'apollon.html')


def sql_query_view(request):
    result = None
    error = None
    columns = []
    rowcount = 0

    if request.method == 'POST':
        form = SQLQueryForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data['query']
            try:
                cursor = runSql(query, request.user.username)
                #with connection.cursor() as cursor:
                #    cursor.execute(query)

                if cursor.description:  # SELECT
                    columns = [col[0] for col in cursor.description]
                    result = cursor.fetchall()
                else:
                    result = f"{cursor.rowcount} Zeile(n) betroffen."
                rowcount = len(result)
            except DatabaseError as e:
                error = str(e)
    else:
        form = SQLQueryForm()

    return render(request, 'sql.html', {
        'form': form,
        'result': result,
        'error': error,
        'columns': columns,
        'rowcount': rowcount
    })

def db_models(request):
    items = DatabaseModel.objects.all()
    return render(request, 'db_models.html', {'models': items})

def upload_json(request):
    if request.method == 'POST' and request.FILES.get('json_file'):
        json_file = request.FILES['json_file']
        data = json.loads(json_file.read().decode('utf-8'))
        print(data)
        # Call your existing extract_tables function to get SQL
        sql_output = format_sql(extract_tables(data))
        DatabaseModel.objects.all().delete()  # Clear previous entries
        DatabaseModel.objects.create(json=data, sql=sql_output)
        
        # Execute the SQL
        #with connection.cursor() as cursor:
        #     for statement in sql_output.split(';'):
        #        statement = statement.strip()
        #        if statement:
        #            cursor.execute(statement)
        
        #return redirect('home')  # or wherever you want to redirect)
        delete_db(request.user.username)  # Delete the old database
        runSql(sql_output, request.user.username)  # Call the function to execute SQL statements
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
    request.session.flush()  # Clear the session data
    return render(request, 'logged_out.html')