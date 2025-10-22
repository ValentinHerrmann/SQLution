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
    get_category = lambda x: x.split(' - ')[0] if ' - ' in x else 'Allgemein'
    sqlfiledict = [{'file': file, 'name': removePrefix(file), 'category': get_category( removePrefix(file)) } for file in sql_files]

    context = {'data': {}}
    for entry in sqlfiledict:
        cat = entry['category']
        if cat not in context['data']:
            context['data'][cat] = []
        context['data'][cat].append(entry)
        
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
                # inpVals: raw submitted values for repopulating the form
                # sqlVals: processed values to insert into the SQL
                inpVals = {}
                sqlVals = {}
                for inp in inputs:
                    val = request.POST.get(f'input_{inp}', '')
                    inpVals[inp] = val
                    sqlVals[inp] = val
                for drop in dropdowns:
                    n = drop['name']
                    raw = request.POST.get(f'dropdown_{n}', '')
                    inpVals[n] = raw

                    # Try to extract a primary value for SQL substitution.
                    # If the dropdown option contains commas (e.g. "1, 'name'") take the first segment.
                    # Otherwise use the raw value directly.
                    if raw is None:
                        raise Exception("Fehler bei der Dropdown-Auswahl. Keine Auswahl übermittelt.")
                    parts = [p.strip() for p in raw.split(',')]
                    if len(parts) >= 1 and parts[0] != '':
                        first = parts[0]
                        # strip surrounding single or double quotes
                        if (first.startswith("'") and first.endswith("'")) or (first.startswith('"') and first.endswith('"')):
                            first = first[1:-1]
                        sqlVals[n] = first
                    else:
                        # fallback
                        sqlVals[n] = raw
            
                sql = re.sub(r'\[[^\]]+\]', '',sql)
                #sql = re.replace(r'\[[^\]]+\]', '', sql)
                # Use processed sqlVals for substitution so SQL gets the correct primary values
                for key, value in sqlVals.items():
                    sql = sql.replace('{' + key + '}', str(value))
                
                
                cursor = runSql(sql, request.user.username)

                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    result = cursor.fetchall()
            except Exception as e:
                error = str(e)
        sql = sql.replace("\n", "<br>")
    return render_user_fun_exec(request, sql, inputs, sqlfile, result, error, columns, dropdowns, inpVals if 'inpVals' in locals() else {})
    
    return render_user_fun_exec(request, '', [], '', [], 'Keine SQL Datei gefunden.', [], [])


def render_user_fun_exec(request, sql, inputs, sqlfile, result, error, columns, dropdowns, inpVals=None):
    result = remove_nones_from_sqlresult(result)
    return render(request, 'user_functions_execute.html', {
        'inputs': inputs,
        'dropdowns': dropdowns,
        'query': sql,
        'title': sqlfile.split('_')[1] if '_' in sqlfile else sqlfile,
        'result': result,
        'error': error,
        'columns': columns,
        'inpVals': inpVals or {},
    })
