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
    path('accounts/login/', views_user.CustomLoginView.as_view(), name='login'),
    path('logged_out/', views_user.logged_out, name='logged_out'),
    path('logged_in/', views_user.logged_in, name='logged_in'),

    path('upload_db/', views_files.upload_db, name='upload_db'),
    path('download_db/', views_files.download_db, name='download_db'),
    path('upload_json/', views_files.upload_json, name='upload_json'),
    path('download_zip/', views_files.download_zip, name='download_zip'),
    path('upload_zip/', views_files.upload_zip, name='upload_zip'),
    
    path('sql/', views.sql_query_view, name='sql'),
    path('overview/', views.overview, name='overview'),
    path('sql_form/', views.sql_form, name='sql_form'),
    
    path('admin_overview/', views_user.admin_overview, name='admin_overview'),
    path('api/system-data/', views_user.get_system_data, name='get_system_data'),

    path('sql_ide/', views.sql_ide, name='sql_ide'),
    path('user_databases.sqlite', views_files.read_file),
    path('user_databases/<str:username>.sqlite', views_files.read_file),

    path('api/sql/<str:filename>.sql', views_files.api_sql, name='api_sql'),
    path('api/sql/all', views_files.api_sql_all, name='api_sql_all'),
    path('api/upload_db/', views_files.api_upload_db, name='api_upload_db')
]