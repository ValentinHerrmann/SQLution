import json
from django.http import HttpResponse, JsonResponse
from django.urls import get_resolver
from myapp.utils.decorators import is_db_admin, is_global_admin
from django.contrib.auth.decorators import login_required,user_passes_test
from myapp.utils.directories import get_user_directory, sqllock_release
from myapp.utils import api_utils
from django.views.decorators.http import require_http_methods


@require_http_methods(['GET'])
def api_endpoints(request) -> HttpResponse:
    """Return a JSON list of all API endpoints."""
    try:
        resolver = get_resolver()
        endpoints = api_utils.extract_api_endpoints(resolver.url_patterns)
        
        # Sort by path for better readability
        endpoints.sort(key=lambda x: x['path'] or '')
        
        return JsonResponse({
            'endpoints': endpoints,
            'count': len(endpoints)
        }, json_dumps_params={'indent': 2})
    except Exception as _:
        return HttpResponse("Could not get endpoints", status=500)

@require_http_methods(['GET', 'POST', 'PUT', 'DELETE'])
@login_required
@user_passes_test(is_db_admin)
def api_sql(request, filename:str) -> HttpResponse:
    user_dir = get_user_directory(request.user.username)
    try:
        if request.method == "PUT" or request.method == "POST":
            body_unicode = request.body.decode('utf-8')
            body = json.loads(body_unicode)
            sql = body['sql']
            api_utils.save_sql_file(user_dir, filename, sql)
            sqllock_release(user_dir)
            return HttpResponse("File saved successfully", status=200)

        if request.method == "GET":
            file_content = api_utils.read_sql_file(user_dir, filename)
            sqllock_release(user_dir)
            return HttpResponse(file_content, content_type="text/sql", status=200)
        
        if request.method == "DELETE":
            deleted = api_utils.delete_sql_file(user_dir, filename)
            sqllock_release(user_dir)
            if deleted:
                return HttpResponse("File deleted successfully", status=200)
            return HttpResponse("File not found", status=404)
        
        return HttpResponse("Internal Server Error", status=500)
    except Exception as e:
        print(f"Error: {e}")
        return HttpResponse("Unknown request", status=500)
    finally:
        sqllock_release(user_dir)

@require_http_methods(['POST'])
@login_required
@user_passes_test(is_db_admin)
def api_sql_all(request) -> HttpResponse:
    from myapp.utils.directories import sqllock_get
    user_dir = get_user_directory(request.user.username)
    try:
        sqllock_get(user_dir)

        if request.method == "POST":
            body_unicode = request.body.decode('utf-8')
            body = json.loads(body_unicode)
            files = body['files']
            
            api_utils.replace_all_sql_files(user_dir, files)
            sqllock_release(user_dir)
            return HttpResponse("Files saved successfully", status=200)
        
        return HttpResponse("Unknown request", status=404)
    except Exception as e:
        print(f"Error: {e}")
        return HttpResponse("Internal error while saving SQL files.", status=500)
    finally:
        sqllock_release(user_dir)


@require_http_methods(['GET'])
@login_required
@user_passes_test(is_db_admin)
def api_sql_list(request) -> HttpResponse:
    """Return a JSON list of SQL filenames for the current user's directory."""
    from myapp.utils.directories import sqllock_get
    user_dir = get_user_directory(request.user.username)
    try:
        sqllock_get(user_dir)
        if request.method == "GET":
            files = api_utils.list_sql_files(user_dir)
            return JsonResponse({'files': files})
        else:
            return HttpResponse("Method not allowed", status=405)
    except Exception as e:
        print(f"Error in api_sql_list: {e}")
        return HttpResponse("Internal error while listing user's SQL files", status=500)
    finally:
        sqllock_release(user_dir)


@require_http_methods(['POST'])
@login_required
@user_passes_test(is_db_admin)
def api_run_sql(request) -> HttpResponse:
    """Execute provided SQL and return JSON with columns/result or error."""
    try:
        if request.method != 'POST':
            return HttpResponse("Method not allowed", status=405)

        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        sql = body.get('sql', '')
        
        result = api_utils.execute_sql_query(sql, request.user.username)
        
        if result['error'] and not sql:
            return JsonResponse(result, status=400)
        elif result['error']:
            # Determine if it's an operational error (400) or server error (500)
            # For now, treat SQL errors as 400 (bad request)
            return JsonResponse(result, status=400)
        else:
            return JsonResponse(result)
    except Exception as e:
        print(f"Error in api_run_sql: {e}")
        return JsonResponse({'columns': [], 'result': [], 'error': str(e)}, status=500)

@require_http_methods(['POST'])
@login_required
@user_passes_test(is_db_admin)
def api_upload_db(request) -> HttpResponse:
    user_dir = get_user_directory(request.user.username)
    try:
        if request.method == "POST":
            api_utils.save_database_file(user_dir, request.body)
            return HttpResponse("File saved successfully", status=201)
    except Exception as e:
        print(f"Error: {e}")
        return HttpResponse("Internal error while uploading database.", status=500)
    return HttpResponse("Method Not Allowed", status=405)

@require_http_methods(['GET', 'POST'])
@login_required
@user_passes_test(is_db_admin)
def api_db_diagram_json(request):
    from myapp.utils.directories import sqllock_get
    user_dir = get_user_directory(request.user.username)
    try:
        sqllock_get(user_dir)
        if request.method == "GET":
            file_content = api_utils.read_diagram_json(user_dir, 'model.json')
            return HttpResponse(file_content, content_type="application/json")
        elif request.method == "POST":
            api_utils.save_diagram_json(user_dir, 'model.json', request.body, 
                                       process_diagram=True, username=request.user.username)
            return HttpResponse("", status=200)
        else:
            return HttpResponse("", status=405)
    except Exception as e:
        print(f"Error: {e}")
        return HttpResponse("Internal error while handling database diagram JSON.", status=500)
    finally:
        sqllock_release(user_dir)
        
        

@require_http_methods(['GET', 'POST'])
@login_required
@user_passes_test(is_db_admin)
def api_editor_diagram_json(request):
    from myapp.utils.directories import sqllock_get
    user_dir = get_user_directory(request.user.username)
    try:
        sqllock_get(user_dir)
        if request.method == "GET":
            file_content = api_utils.read_diagram_json(user_dir, 'editor_model.json')
            return HttpResponse(file_content, content_type="application/json")
        elif request.method == "POST":
            api_utils.save_diagram_json(user_dir, 'editor_model.json', request.body)
            return HttpResponse("", status=200)
        else:
            return HttpResponse("", status=405)
    except Exception as e:
        print(f"Error: {e}")
        return HttpResponse("Internal error while handling editor diagram JSON.", status=500)
    finally:
        sqllock_release(user_dir)

@require_http_methods(['GET'])
@login_required
@user_passes_test(is_global_admin)
def get_system_data(request) -> HttpResponse:
    from myapp.utils.utils import timestamp
    print(f"{timestamp()}get_system_data endpoint called by {request.user.username}")
    
    try:
        # Collect all system data
        response_data = api_utils.collect_system_data()
        
        # Log data and perform rotation check
        api_utils.log_and_rotate_system_data(response_data)
        
        # Return data as JSON
        return JsonResponse(response_data)
    except Exception as e:
        print(f"{timestamp()}Error in get_system_data: {e}")
        return HttpResponse("Internal error while collecting system data", status=500)

@require_http_methods(['POST'])
@login_required
def api_resolve_subqueries(request) -> HttpResponse:
    try: 
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        sql = body.get('sql', '')
        sql = api_utils.resolve_subqueries(sql, request.user.username)
        return HttpResponse(sql, content_type="text/sql", status=200)
    except RecursionError as re:
        print(f"RecursionError in resolve_subqueries: {re}")
        return HttpResponse("Error: Maximum subquery nesting depth reached. Possible circular reference detected.", status=400)
    except Exception as e:
        print(f"{timestamp()}Error in resolve_subqueries: {e}")
        return HttpResponse("Internal error while resolving subqueries", status=500)
