from django.http import HttpResponse
from django.shortcuts import render
from myapp.views.forms import *
from myapp.utils.utils import *
from myapp.utils.decorators import *
from myapp.models import *
from myapp.utils.directories import fullpath
from myapp.views.helpers import *
from myapp.utils.sqlite_connector import * 

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect
from django.conf import settings
from PIL import Image
import os
import re
import qrcode
import qrcode.image.svg
import qrcode.constants
try:
    from qrcode.image.styledpil import StyledPilImage
    STYLED_PIL_AVAILABLE = True
except ImportError:
    STYLED_PIL_AVAILABLE = False
import io
import base64
import xml.etree.ElementTree as ET





@login_required
def sql_form(request):    
    error = ''
    result = []
    columns = []

    # Get the list of tables in the database
    sqlfile = request.GET.get("file")

    if sqlfile is not None and sqlfile != '':
        dir = get_user_directory(request.user.username)


        
        with open(fullpath(dir,f"{sqlfile}.sql"), "r") as f:
            sql = f.read()
            sql += ';'
        inputs = re.findall(r'{([^}]+)}\w?[^\[]', sql)

        inputs = list(dict.fromkeys(inputs))
        
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

        # Remove entries from inputs that are also present as names in dropdowns
        dropdown_names = {drop['name'] for drop in dropdowns}
        inputs = [inp for inp in inputs if inp not in dropdown_names]

        

        if request.method == 'POST' or len(inputs)+len(dropdowns) == 0:
            try:
                inpVals = {}
                for inp in inputs:
                    inpVals[inp] = request.POST.get(f'input_{inp}')
                for drop in dropdowns:
                    n = drop['name']
                    v = request.POST.get(f'dropdown_{n}')
                    # v = v.replace("(", "").replace(")", "")
                    v = v.split(",")
                    if len(v) > 1:
                        # Remove leading and trailing single quotes if both exist
                        if v[0].startswith("'") and v[0].endswith("'"):
                            inpVals[n] = v[0][1:-1]
                        else:
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
                elif not error and cursor: # write query
                    result = ""
                    rowcount = f"{cursor.rowcount} Zeile(n) verändert."
                try:
                    if query.strip().upper().startswith("INSERT INTO"):
                        table_name = query.split()[2]
                        select_query = f"SELECT * FROM {table_name}"
                        cursor, columns, result, error = execute_sql_query(select_query, request.user.username)
                except Exception as e:
                    pass

            if save=='on' and sqlfile and sqlfile != '':
                dir = get_user_directory(request.user.username)
                with open(fullpath(dir,f"{sqlfile}.sql"), "w") as f:
                    f.write(query)
                error = f"Die SQL-Abfrage wurde erfolgreich unter '{sqlfile}' gespeichert."
                

    else:
        queryForm = load_sql_queryfile(request)
        sqlfile = request.GET.get("file")
        delete = request.GET.get('delete')
        if delete:
            error = f"Die SQL-Abfrage '{sqlfile}' in den Editor geladen und anschließend gelöscht."
            dir = get_user_directory(request.user.username)
            if os.path.exists(fullpath(dir,f"{sqlfile}.sql")):
                os.remove(fullpath(dir,f"{sqlfile}.sql"))


    return render_sql(request, queryForm, result, error, columns, rowcount, table_scheme_html, sqlfile)

@login_required
@user_passes_test(is_db_admin)
def overview(request):
    tables = []

    cursor = runSql("SELECT name FROM sqlite_master WHERE type='table' AND NOT name LIKE 'sqlite_%';", request.user.username)
    if(cursor is None):
        return render(request, 'overview.html', {
            'models': None,
            'functions': None
        })
    
    tablenames = [row[0] for row in cursor.fetchall()]

    for t in tablenames:
        cursor11 = runSql(f"SELECT * FROM {t} LIMIT 11;", request.user.username)
        cursor10 = runSql(f"SELECT * FROM {t} LIMIT 10;", request.user.username)
        c10_result = remove_nones_from_sqlresult(cursor10.fetchall())
        tables.append(
            {
                'name': t,
                'columns': [col[0] for col in cursor10.description],
                'rows': c10_result + ([['. . .' for _ in cursor10.description]] if len(cursor11.fetchall()) > len(c10_result) else [])
            }
        )

    
    
    sql = []
    dir = get_user_directory(request.user.username)
    sql_files = []
    if os.path.exists(dir):
        sql_files = [file for file in os.listdir(dir) if file.endswith('.sql')]
        
    for file in sql_files:
        with open(f"{dir}/{file}", "r") as f:
            sql.append({
                'name': file.removesuffix('.sql'),
                'sql': f.read().replace(';',';<br>\n'),
            })



    return render(request, 'overview.html', {
        'models': tables,
        'functions': sql
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

