
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from myapp.models import *
from myapp.utils.utils import *
from myapp.utils.sqlite_connector import *
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect
from myapp.utils.decorators import *
from myapp.utils.directories import *
import os



@login_required
def home(request):
    if is_global_admin(request.user):
        return redirect('admin_overview')
    elif is_db_admin(request.user):
        return redirect('overview')  
    else:
        return redirect('user_functions')  
    

@login_required
@user_passes_test(is_db_admin)
def apollon(request):
    upload_max_bytes = getattr(__import__('django.conf').conf.settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', None)
    def human_readable(num):
        for unit in ['B','KB','MB','GB','TB']:
            if abs(num) < 1024.0:
                return "%3.1f %s" % (num, unit)
            num /= 1024.0
        return "%3.1f %s" % (num, 'PB')
    upload_max_human = human_readable(upload_max_bytes) if upload_max_bytes else None
    return render(request, 'apollon.html', {
        'upload_max_bytes': upload_max_bytes,
        'upload_max_human': upload_max_human,
    })
    

def actuator_gateway_routes(request):
    """Compatibility endpoint for platform probes expecting Spring Boot actuator."""
    if request.method != 'GET':
        return JsonResponse({'detail': 'Method not allowed'}, status=405)

    return JsonResponse({
        'application': 'sqlution',
        'component': 'gateway',
        'routes': [],
        'status': 'ok'
    })

