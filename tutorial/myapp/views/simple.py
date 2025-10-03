
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
    return render(request, 'apollon.html')
    
@login_required
def user_functions(request):
    dir = get_user_directory(request.user.username)
    suffix = get_user_suffix(request.user.username)
    sql_files = []
    if os.path.exists(dir):
        accessAllowed = lambda x: suffix=='' or '_' not in x or x.startswith(suffix+'_')
        sql_files = [file[:-4] for file in os.listdir(dir) if file.endswith('.sql') and accessAllowed(file)]
    sql_files.sort()

    removedPrefix = lambda x: x.split('_')[1] if '_' in x else x 
    sqlfiledict = [{'file': file, 'name': removedPrefix(file) } for file in sql_files]

    context = {'sqlfiles': sqlfiledict}
    return render(request, 'user_functions.html', context)
