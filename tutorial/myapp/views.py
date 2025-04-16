
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

def apollon(request):
    return render(request, 'apollon.html')


def sql_query_view(request):
    result = None
    error = None
    columns = []
    rowcount = 0

    html_output = convert_sqlite_master_to_html(request.user.username)
    print(html_output)


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

                    if query.strip().upper().startswith("INSERT INTO"):
                        table_name = query.split()[2]
                        select_query = f"SELECT * FROM {table_name}"
                        cursor = runSql(select_query, request.user.username)
                        columns = [col[0] for col in cursor.description]
                        result = cursor.fetchall()

            except DatabaseError as e:
                error = str(e)
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

    cursor = runSql("SELECT name FROM sqlite_master WHERE type='table';", request.user.username)
    tablenames = [row[0] for row in cursor.fetchall()]

    for t in tablenames:
        cursor = runSql(f"SELECT * FROM {t};", request.user.username)
        tables.append(
            {
            'name': t,
            'columns': [col[0] for col in cursor.description],
            'rows': cursor.fetchall()
            }
        )

    models = [
        {
            "columns": ["ID", "Name", "Age"],
            "rows": [
                [1, "Alice", 30],
                [2, "Bob", 25],
            ],
        },
        {
            "columns": ["ID", "Title", "Author"],
            "rows": [
                [1, "Book A", "Author A"],
                [2, "Book B", "Author B"],
            ],
        },
    ]

    return render(request, 'db_models.html', {
        'models': tables
    })

def upload_json(request):
    if request.method == 'POST' and request.FILES.get('json_file'):
        json_file = request.FILES['json_file']
        try:
            data = json.loads(json_file.read().decode('utf-8'))
            print(data)
            # Call your existing extract_tables function to get SQL
            sql_output = format_sql(extract_tables(data))
            binaryDB = create_db(sql_output, request.user.username)  # Call the function to execute SQL statements

            DatabaseModel.objects.filter(user=request.user.username).delete()  # Delete old entries for the user
            DatabaseModel.objects.create(user=request.user.username,json=data, sql=sql_output, db=binaryDB)  # Create a new entry with the binary data
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
    request.session.flush()  # Clear the session data
    return redirect('home')  # Redirect to the home page
    return render(request, 'logged_out.html')