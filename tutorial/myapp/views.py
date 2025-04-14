
from django.shortcuts import render, redirect
from django.db import connection, DatabaseError
from django.apps import apps
from .forms import SQLQueryForm
from .models import TodoItem
from .utils import *  # Assuming you have this function in utils.py
import json


# Create your views here.
def home(request):
    tables = [m._meta.db_table for c in apps.get_app_configs() for m in c.get_models()]
    return render(request, 'home.html', {'tables': tables})

def todos(request):
    items = TodoItem.objects.all()
    return render(request, 'todos.html', {'todos': items})


def sql_query_view(request):
    result = None
    error = None
    columns = []

    if request.method == 'POST':
        form = SQLQueryForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data['query']
            try:
                with connection.cursor() as cursor:
                    cursor.execute(query)

                    if cursor.description:  # SELECT
                        columns = [col[0] for col in cursor.description]
                        result = cursor.fetchall()
                    else:
                        result = f"{cursor.rowcount} Zeile(n) betroffen."
            except DatabaseError as e:
                error = str(e)
    else:
        form = SQLQueryForm()

    return render(request, 'sql.html', {
        'form': form,
        'result': result,
        'error': error,
        'columns': columns,
    })


def upload_json(request):
    if request.method == 'POST' and request.FILES.get('json_file'):
        json_file = request.FILES['json_file']
        data = json.loads(json_file.read().decode('utf-8'))
        print(data)
        # Call your existing extract_tables function to get SQL
        sql_output = extract_tables(data)
        
        print(sql_output)

        sql_output = format_sql(sql_output)
        
        print(sql_output)
        
        # Execute the SQL
        #with connection.cursor() as cursor:
        #     for statement in sql_output.split(';'):
        #        statement = statement.strip()
        #        if statement:
        #            cursor.execute(statement)
        
        #return redirect('home')  # or wherever you want to redirect

    return render(request, 'upload_json.html', {'sqlquery': sql_output})