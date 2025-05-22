

from django.http import HttpResponse
from django.shortcuts import render
from .forms import SQLFileForm, SQLQueryForm
from .models import *
from .utils import *  # Assuming you have this function in utils.py
from .views_helpers import *
from .sqlite_connector import *  # Import sqlite3 for SQLite database connection
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect
import os
import re





@login_required
def sql_form(request):    
    error = ''
    result = []
    columns = []

    # Get the list of tables in the database
    sqlfile = request.GET.get("file")

    if sqlfile is not None and sqlfile != '':
        dir = get_user_directory(request.user.username)
        with open(f"{dir}/{sqlfile}.sql", "r") as f:
            sql = f.read()
            sql += ';'
        inputs = re.findall(r'{([^}]+)}\w?[^\[]', sql)

        
        dropdownSQLs = re.findall(r'({[^}]+}\[[^\]]+\])', sql)
        dropdowns = []
        for drop in dropdownSQLs:
            name = re.findall(r'{(.*?)}', drop)[0]
            dSql = re.findall(r'\[(.*?)\]', drop)[0]
            cur = runSql(dSql, request.user.username)
            vals = cur.fetchall()
            v = [str(row).replace("(", "").replace(")", "") for row in vals]
            dropdowns.append({
                'name': name,
                'options': v
            })

        if request.method == 'POST':
            try:
                print(request.POST.keys())
                inpVals = {}
                for inp in inputs:
                    inpVals[inp] = request.POST.get(f'input_{inp}')
                for drop in dropdowns:
                    n = drop['name']
                    v = request.POST.get(f'dropdown_{n}')
                    # v = v.replace("(", "").replace(")", "")
                    v = v.split(",")
                    if len(v) > 1:
                        inpVals[n] = v[0]
                    else:
                        raise Exception("Fehler bei der Dropdown-Auswahl. Kein Primärschlüssel gefunden.")
            
                sql = re.sub(r'\[[^\]]+\]', '',sql)
                #sql = re.replace(r'\[[^\]]+\]', '', sql)
                for key, value in inpVals.items():
                    sql = sql.replace('{' + key + '}', value)
                
                
                cursor = runSql(sql, request.user.username)

                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    result = cursor.fetchall()
            except Exception as e:
                error = str(e)
        sql = sql.replace("\n", "<br>")
        return render_sql_form(request, sql, inputs, sqlfile, result, error, columns, dropdowns)
    
    return render_sql_form(request, '', [], '', [], 'Keine SQL Datei gefunden.', [], [])


@login_required
@user_passes_test(is_db_admin)
def sql_query_view(request):
    result = None
    error = None
    columns = []
    rowcount = -1
    sqlfile = ''

    table_scheme_html = convert_sqlite_master_to_html(request.user.username)

    
    if request.method == 'POST':
        queryForm = SQLQueryForm(request.POST)
        sqlfile = request.POST.get('input_filename')
        save = request.POST.get('save_query')

            




        if queryForm.is_valid():
            query = queryForm.cleaned_data['query']
            query = query.replace("“", "\"").replace("„", "\"").replace("‚", "'").replace("’", "'").replace("‘", "'")

            
            inputs = re.findall(r'{(.*?)}', query)
            if len(inputs) > 0:
                error = "Die SQL-Abfrage enthält {Platzhalter}. Ersetze die Platzhalter mit Werten, um sie auszuführen oder benutze die Nutzerfunktionen."
            else:
                cursor, columns, result, error = execute_sql_query(query, request.user.username)
                if not error and cursor and cursor.description: # read query
                    rowcount = f"{len(result)} Zeile(n) gefunden."
                elif not error: # write query
                    result = ""
                    rowcount = f"{cursor.rowcount} Zeile(n) verändert."
                try:
                    if query.strip().upper().startswith("INSERT INTO"):
                        table_name = query.split()[2]
                        select_query = f"SELECT * FROM {table_name}"
                        cursor, columns, result, error = execute_sql_query(select_query, request.user.username)
                except Exception as e:
                    print(str(e))

            if save=='on' and sqlfile and sqlfile != '':
                dir = get_user_directory(request.user.username)
                with open(f"{dir}/{sqlfile}.sql", "w") as f:
                    f.write(query)
                error = f"Die SQL-Abfrage wurde erfolgreich unter '{sqlfile}' gespeichert."
                

    else:
        queryForm = load_sql_queryfile(request)
        sqlfile = request.GET.get("file")
        delete = request.GET.get('delete')
        if delete:
            error = f"Die SQL-Abfrage '{sqlfile}' in den Editor geladen und anschließend gelöscht."
            dir = get_user_directory(request.user.username)
            if os.path.exists(f"{dir}/{sqlfile}.sql"):
                os.remove(f"{dir}/{sqlfile}.sql")


    return render_sql(request, queryForm, result, error, columns, rowcount, table_scheme_html, sqlfile)


@login_required
@user_passes_test(is_db_admin)
def db_models(request):
    tables = []

    cursor = runSql("SELECT name FROM sqlite_master WHERE type='table' AND NOT name LIKE 'sqlite_%';", request.user.username)
    if(cursor is None):
        return render(request, 'db_models.html', {
            'models': None
        })
    
    tablenames = [row[0] for row in cursor.fetchall()]

    for t in tablenames:
        cursor11 = runSql(f"SELECT * FROM {t} LIMIT 11;", request.user.username)
        cursor10 = runSql(f"SELECT * FROM {t} LIMIT 10;", request.user.username)
        c10_result = cursor10.fetchall()

        tables.append(
            {
                'name': t,
                'columns': [col[0] for col in cursor10.description],
                'rows': c10_result + ([['. . .' for _ in cursor10.description]] if len(cursor11.fetchall()) > len(c10_result) else [])
            }
        )

    return render(request, 'db_models.html', {
        'models': tables
    })




@login_required
@user_passes_test(is_db_admin)
def sql_ide(request):
    
    sql = []
    dir = get_user_directory(request.user.username)
    sql_files = []
    if os.path.exists(dir):
        sql_files = [file for file in os.listdir(dir) if file.endswith('.sql')]
        
    for file in sql_files:
        with open(f"{dir}/{file}", "r") as f:
            sql.append({
                'filename': file,
                'content': f.read(),
            })

    tablescheme = convert_sqlite_master_to_html(request.user.username)
    pars = {
        'user_url': f'/user_databases/{request.user.username}.sqlite',
        'user_name': request.user.username,
        'tablescheme': tablescheme,
        'sql_files': sql
    }
    return render(request, 'sql_ide.html', pars)

