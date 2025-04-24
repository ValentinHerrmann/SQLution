from django.shortcuts import render


from .forms import SQLQueryForm
from .sqlite_connector import runSql
from .models import *
from .utils import *
import os
import zipfile
from io import BytesIO




def is_db_admin(user):
    return user.is_authenticated and user.username.endswith('_admin')

def execute_sql_query(query, username):
    try:
        cursor = runSql(query, username)
        if cursor and cursor.description:
            columns = [col[0] for col in cursor.description]
            result = cursor.fetchall()
            return cursor, columns, result, None
        else:
            return cursor, [], {}, 'Kein Eergebnis gefunden.'
    except Exception as e:
        return None, [], {}, str(e)
    

def render_sql_form(request, sql, inputs, sqlfile, result, error, columns):
    return render(request, 'sql_form.html', {
        'inputs': inputs,
        'query': sql,
        'title': sqlfile,
        'result': result,
        'error': error,
        'columns': columns,
    })


def render_sql(request, form, result, error, columns, rowcount, tablescheme, file):
    if file is None:
        file = ''
    return render(request, 'sql.html', {
        'queryForm': form,
        'result': result,
        'error': error,
        'columns': columns,
        'rowcount': rowcount,
        'tablescheme': tablescheme,
        'file': file,
    })

def load_sql_queryfile(request):
    form = SQLQueryForm()
        
    sqlfile = request.GET.get("file")
    if sqlfile is None: 
        sqlfile = ''
    if sqlfile and sqlfile != '':
        dir = get_user_directory(request.user.username)
        with open(f"{dir}/{sqlfile}.sql", "r") as f:
            sql = f.read()
        form = SQLQueryForm(initial={'query': sql})
    return form


