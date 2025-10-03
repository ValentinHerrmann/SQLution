from django.urls import include, path, re_path
from myapp.views import api,files,simple,user,views,admin,user_functions
from myapp import views_user
from django.views.generic import RedirectView
favicon_view = RedirectView.as_view(url='/static/favicon.ico', permanent=True)

urlpatterns = [
    re_path(r'^favicon\.ico$', favicon_view),
    path('', simple.home, name='home'),
    path('apollon/', simple.apollon, name='apollon'),
    path('user_functions/', user_functions.user_functions, name='user_functions'),
    path('user_functions/execute/', user_functions.user_functions_execute, name='user_functions_execute'),
    
    #path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/login/', user.CustomLoginView.as_view(), name='login'),
    path('logged_out/', user.logged_out, name='logged_out'),
    path('logged_in/', user.logged_in, name='logged_in'),

    path('upload_db/', files.upload_db, name='upload_db'),
    path('download_db/', files.download_db, name='download_db'),
    path('upload_json/', files.upload_json, name='upload_json'),
    path('download_zip/', files.download_zip, name='download_zip'),
    path('upload_zip/', files.upload_zip, name='upload_zip'),
    
    # path('sql/', views.sql_query_view, name='sql'),
    path('overview/', views.overview, name='overview'),
    

    path('qr_generator/', admin.qr_generator, name='qr_generator'),
    path('admin_overview/', admin.admin_overview, name='admin_overview'),
    path('api/system-data/', api.get_system_data, name='get_system_data'),
    path('download-resource-logs/', user.download_resource_logs, name='download_resource_logs'),
    path('download-audit-logs/', views_user.download_audit_logs, name='download_audit_logs'),
    path('clear-resource-logs/', views_user.clear_resource_logs, name='clear_resource_logs'),
    path('clear-audit-logs/', views_user.clear_audit_logs, name='clear_audit_logs'),
    path('end-all-sessions/', user.end_all_sessions, name='end_all_sessions'),

    path('sql_ide/', views.sql_ide, name='sql_ide'),
    path('user_databases.sqlite', files.read_file),
    path('user_databases/<str:username>.sqlite', files.read_file),

    path('api/sql/<str:filename>.sql', api.api_sql, name='api_sql'),
    path('api/sql/all', api.api_sql_all, name='api_sql_all'),
    path('api/upload_db/', api.api_upload_db, name='api_upload_db'),
    path('api/diagram.json', api.api_diagram_json, name='api_diagram_json'),
]