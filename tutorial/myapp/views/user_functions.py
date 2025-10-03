from django.shortcuts import get_object_or_404, render, redirect
from myapp.models import *
from myapp.utils.utils import *
from myapp.utils.sqlite_connector import *
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import redirect
from myapp.utils.decorators import *
from myapp.utils.directories import *
import os



@login_required
def user_functions(request):
    dir = get_user_directory(request.user.username)
    suffix = get_user_suffix(request.user.username)
    sql_files = []
    if os.path.exists(dir):
        accessAllowed = lambda x: suffix=='' or '_' not in x or x.startswith(suffix+'_')
        sql_files = [file[:-4] for file in os.listdir(dir) if file.endswith('.sql') and accessAllowed(file)]
    sql_files.sort()

    removePrefix = lambda x: x.split('_')[1] if '_' in x else x 
    sqlfiledict = [{'file': file, 'name': removePrefix(file) } for file in sql_files]

    context = {'sqlfiles': sqlfiledict}
    return render(request, 'user_functions.html', context)


@login_required
def user_functions_execute(request):    
    error = ''
    result = []
    columns = []

    # Get the list of tables in the database
    sqlfile = request.GET.get("file")

    if sqlfile is not None and sqlfile != '':
        dir = get_user_directory(request.user.username)
        suffix = get_user_suffix(request.user.username)
        accessAllowed = lambda x: suffix=='' or '_' not in x or x.startswith(suffix+'_')
        if not accessAllowed(sqlfile+'.sql'):
            logout(request)
            messages.error(request, 'Du hast versucht auf eine SQL-Abfrage zuzugreifen, auf die du nicht zugreifen darfst. Du wurdest aus Sicherheitsgründen abgemeldet.')
            return redirect('login')
        
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
        return render_user_fun_exec(request, sql, inputs, sqlfile, result, error, columns, dropdowns)
    
    return render_user_fun_exec(request, '', [], '', [], 'Keine SQL Datei gefunden.', [], [])


def render_user_fun_exec(request, sql, inputs, sqlfile, result, error, columns, dropdowns):
    result = remove_nones_from_sqlresult(result)
    return render(request, 'user_functions_execute.html', {
        'inputs': inputs,
        'dropdowns': dropdowns,
        'query': sql,
        'title': sqlfile.split('_')[1] if '_' in sqlfile else sqlfile,
        'result': result,
        'error': error,
        'columns': columns,
    })
