
import pprint
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.db import connection, DatabaseError
from django.apps import apps
import form_designer
from .forms import SQLQueryForm,UploadFileForm
from .models import *
from .utils import *  # Assuming you have this function in utils.py
from .sqlite_connector import *  # Import sqlite3 for SQLite database connection
import json
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib.auth import logout
import os
import re


@login_required
def download_db(request):
    try:
        db_file = open(get_db_name(request.user.username), "rb").read()
        response = HttpResponse(db_file, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="datenbank_{datetime.now().strftime("%Y-%m-%d_%H-%M")}.db"'
        return response
    except DatabaseModel.DoesNotExist:
        return redirect('db_models')  # Redirect if no database exists for the user
    return redirect('db_models')

@login_required
def upload_db(request):
    #print("Upload DB")
    if request.method == "POST" and request.FILES.get('db_file'):
        db_file = request.FILES['db_file']
        with open(get_db_name(request.user.username), "wb+") as destination:
            for chunk in db_file.chunks():
                destination.write(chunk)
    return redirect('db_models')

@login_required
def upload_json(request):
    if request.method == 'POST' and request.FILES.get('json_file'):
        json_file = request.FILES['json_file']
        try:
            data = json.loads(json_file.read().decode('utf-8'))

            # Call your existing extract_tables function to get SQL
            sql_output = format_sql(extract_tables(data))
            binaryDB = create_db(sql_output, request.user.username)  # Call the function to execute SQL statements

            if DatabaseModel.objects.filter(user=request.user.username).exists():
                db_model = DatabaseModel.objects.get(user=request.user.username)
                db_model.json = data
                db_model.sql = sql_output
                db_model.db = binaryDB
                db_model.save()  # Update the existing entry with the new data
            else:
                DatabaseModel.objects.create(user=request.user.username,json=data, sql=sql_output, db=binaryDB, updated_at=str(datetime.now()))  # Create a new entry with the binary data
            DatabaseModel.save_base()

            #DatabaseModel.objects.filter(user=request.user.username).delete()  # Delete old entries for the user
            #DatabaseModel.objects.create(user=request.user.username,json=data, sql=sql_output, db=binaryDB)  # Create a new entry with the binary data
        except:
            return redirect('apollon')  # Redirect to home if error occurs
    return redirect('db_models')  # Redirect to home after processing
    #return render(request, 'upload_json.html', {'sqlquery': sql_output})
