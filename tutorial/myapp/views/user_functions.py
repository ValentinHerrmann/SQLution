from django.http import HttpResponse
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
from myapp.utils.api_utils import *
from myapp.utils.pdf_export import build_result_pdf, pdf_filename
from myapp.utils import query_access
from myapp.utils.placeholders import find_dropdowns, find_inputs, strip_dropdown_sql, substitute_placeholders
from html import escape
import re
import os



def viewer_suffix(request) -> str:
    """The db-user short name whose queries are shown ('' = all queries).

    While a group admin reviews a db-user, that db-user's name; otherwise the own one.
    """
    return getattr(request.user, 'review_as_db_user', '') or get_user_suffix(request.user.username)


@login_required
def user_functions(request):
    dir = get_user_directory(request.user.username)
    suffix = viewer_suffix(request)
    if suffix == '':
        sql_files = query_access.list_converted_queries(dir)  # db-admin: everything
    else:
        sql_files = query_access.visible_queries(dir, suffix)  # db-user: what the db-admin released

    context = {'data': {}}
    for file in sql_files:
        category, label = query_access.split_category(file)  # the category is the heading (issue #161)
        context['data'].setdefault(category, []).append({'file': file, 'name': label})
        
    return render(request, 'user_functions.html', context)


@login_required
def user_functions_execute(request):    
    error = ''
    result = []
    columns = []

    try:
        # Get the list of tables in the database
        sqlfile = request.GET.get("file")

        # If no SQL file was specified, return a clear error instead of causing an UnboundLocalError.
        if not sqlfile:
            return HttpResponse("No SQL file specified.", status=400)
        if sqlfile is not None and sqlfile != '':
            dir = get_user_directory(request.user.username)
            suffix = viewer_suffix(request)
            if suffix != '' and not query_access.can_see(query_access.load_access(dir), sqlfile, suffix):
                logout(request)
                messages.error(request, 'Du hast versucht auf eine SQL-Abfrage zuzugreifen, auf die du nicht zugreifen darfst. Du wurdest aus Sicherheitsgründen abgemeldet.')
                return redirect('login')
            
            with open(fullpath(dir,f"{sqlfile}.sql"), "r") as f:
                sql = f.read()

            try:

                sql = resolve_subqueries(sql, request.user.username)  # Resolve subqueries before extracting inputs and dropdowns
            except RecursionError as e:
                print(f"RecursionError in resolve_subqueries: {e}")
                return HttpResponse("Error: Maximum subquery nesting depth reached. Possible circular reference detected.", status=400)

            inputs = find_inputs(sql)

            dropdowns = []
            for name, dSql in find_dropdowns(sql):
                if name in [drop['name'] for drop in dropdowns]:
                    continue
                cur = runSql(dSql, request.user.username)
                options = [{
                    'value': '' if row[0] is None else str(row[0]),
                    'label': ', '.join('' if c is None else str(c) for c in row),
                } for row in cur.fetchall()]
                dropdowns.append({
                    'name': name,
                    'options': options
                })

            sql = strip_dropdown_sql(sql)

            if request.method == 'POST' or len(inputs)+len(dropdowns) == 0:
                try:
                    # inpVals: raw submitted values for repopulating the form; they are also the values for the SQL
                    inpVals = {}
                    for inp in inputs:
                        inpVals[inp] = request.POST.get(f'input_{inp}', '')
                    for drop in dropdowns:
                        n = drop['name']
                        inpVals[n] = request.POST.get(f'dropdown_{n}', '')

                    sql = substitute_placeholders(sql, inpVals)

                    cursor = runSql(sql, request.user.username)

                    if cursor.description:
                        columns = [col[0] for col in cursor.description]
                        result = cursor.fetchall()
                except Exception as e:
                    error = str(e)
            sql = escape(sql).replace("\n", "<br>")
        export = request.POST.get('export') or request.GET.get('export')
        return render_user_fun_exec(request, sql, inputs, sqlfile, result, error, columns, dropdowns, inpVals if 'inpVals' in locals() else {}, export)
    except Exception as e:
        error = str(e)
        response = HttpResponse(error, content_type='text/plain')
        response.status_code = 500
        return response


def render_user_fun_exec(request, sql, inputs, sqlfile, result, error, columns, dropdowns, inpVals=None, export=None):
    result = remove_nones_from_sqlresult(result)
    title = sqlfile
    if export == 'pdf' and columns and not error:
        response = HttpResponse(build_result_pdf(title, columns, result), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{pdf_filename(title)}"'
        return response
    return render(request, 'user_functions_execute.html', {
        'inputs': inputs,
        'dropdowns': dropdowns,
        'query': sql,
        'title': title,
        'result': result,
        'error': error,
        'columns': columns,
        'inpVals': inpVals or {},
    })
