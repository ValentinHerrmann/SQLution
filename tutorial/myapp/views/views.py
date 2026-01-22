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
@user_passes_test(is_db_admin)
def overview(request):
    html_template = 'overview.html'
    try:
        tables = []

        cursor = runSql("SELECT name FROM sqlite_master WHERE type='table' AND NOT name LIKE 'sqlite_%';", request.user.username)
        if(cursor is None):
            return render(request, html_template, {
                'models': None,
                'functions': None
            })
        
        tablenames = [row[0] for row in cursor.fetchall()]

        for t in tablenames:
            try:
                cursor11 = runSql(f"SELECT * FROM {t} LIMIT 6;", request.user.username)
                cursor10 = runSql(f"SELECT * FROM {t} LIMIT 5;", request.user.username)
                c10_result = remove_nones_from_sqlresult(cursor10.fetchall())
                tables.append(
                    {
                        'name': t,
                        'columns': [col[0] for col in cursor10.description],
                        'rows': c10_result + ([['. . .' for _ in cursor10.description]] if len(cursor11.fetchall()) > len(c10_result) else [])
                    }
                )
            except Exception as e:
                print(f"Error fetching data for table {t}: {e}")
                tables.append(
                    {
                        'name': t,
                        'columns': [],
                        'rows': [['Fehler beim Abrufen der Tabelle. Das passiert typischerweise, wenn ein Tabellenname ungültig ist. Überprüfe dein Datenbankschema!']]
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



        # pass upload size limits to the template so forms can enforce/display them
        upload_max_bytes = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', None)
        # human readable
        def human_readable(num):
            for unit in ['B','KB','MB','GB','TB']:
                if abs(num) < 1024.0:
                    return "%3.1f %s" % (num, unit)
                num /= 1024.0
            return "%3.1f %s" % (num, 'PB')

        upload_max_human = human_readable(upload_max_bytes) if upload_max_bytes else None
        
        
        tablescheme = convert_sqlite_master_to_html(request.user.username)

        return render(request, html_template, {
            'models': tables,
            'functions': sql,
            'upload_max_bytes': upload_max_bytes,
            'upload_max_human': upload_max_human,
            'tablescheme': tablescheme,
        })
    except Exception as e:
        print(f"Error in overview view: {e}")
        return render(request, html_template, {
            'models': [],
            'functions': [],
            'upload_max_bytes': None,
            'upload_max_human': None,
            'tablescheme': []
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

