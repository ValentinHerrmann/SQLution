from django.shortcuts import render
from myapp.views.forms import *
from myapp.utils.sqlite_connector import *
from myapp.models import *
from myapp.utils.utils import *
from myapp.utils.directories import *



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
    

def render_user_fun_exec(request, sql, inputs, sqlfile, result, error, columns, dropdowns):
    result = remove_nones_from_sqlresult(result)
    return render(request, 'user_functions_execute.html', {
        'inputs': inputs,
        'dropdowns': dropdowns,
        'query': sql,
        'title': sqlfile,
        'result': result,
        'error': error,
        'columns': columns,
    })


# def render_sql(request, form, result, error, columns, rowcount, tablescheme, file):
#     if file is None:
#         file = ''
#     return render(request, 'sql.html', {
#         'queryForm': form,
#         'result': result,
#         'error': error,
#         'columns': columns,
#         'rowcount': rowcount,
#         'tablescheme': tablescheme,
#         'file': file,
#     })

def load_sql_queryfile(request):
    form = SQLQueryForm()
        
    sqlfile = request.GET.get("file")
    if sqlfile is None: 
        sqlfile = ''
    if sqlfile and sqlfile != '':
        dir = get_user_directory(request.user.username)
        with open(fullpath(dir,f"{sqlfile}.sql"), "r") as f:
            sql = f.read()
        form = SQLQueryForm(initial={'query': sql})
    return form


