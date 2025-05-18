from django.urls import include, path, re_path
from . import views, views_user, views_simple, views_files
from django.views.generic import RedirectView
favicon_view = RedirectView.as_view(url='/static/favicon.ico', permanent=True)

urlpatterns = [
    re_path(r'^favicon\.ico$', favicon_view),
    path('', views_simple.home, name='home'),
    path('apollon/', views_simple.apollon, name='apollon'),
    path('user_functions', views_simple.user_functions, name='user_functions'),
    
    path('accounts/', include('django.contrib.auth.urls')),
    path('logged_out/', views_user.logged_out, name='logged_out'),
    path('logged_in/', views_user.logged_in, name='logged_in'),

    path('upload_db/', views_files.upload_db, name='upload_db'),
    path('download_db/', views_files.download_db, name='download_db'),
    path('upload_json/', views_files.upload_json, name='upload_json'),
    path('download_zip/', views_files.download_zip, name='download_zip'),
    path('upload_zip/', views_files.upload_zip, name='upload_zip'),
    
    path('sql/', views.sql_query_view, name='sql'),
    path('db_models/', views.db_models, name='db_models'),
    path('sql_form/', views.sql_form, name='sql_form'),

    
    path('sql_ide_iframe/', views.sql_ide_iframe, name='sql_ide_iframe'),
    path('sql_ide/', views.sql_ide, name='sql_ide'),
    
    path('admin_overview/', views_user.admin_overview, name='admin_overview'),
    path('api/system-data/', views_user.get_system_data, name='get_system_data'),

    path('user_databases.sqlite', views_files.read_file),
    path('user_databases/Dachau.sql', views_files.read_file_sql),
]