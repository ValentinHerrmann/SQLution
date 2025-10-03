
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
    
