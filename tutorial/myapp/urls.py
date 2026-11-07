from django.urls import include, path, re_path
from myapp.views import api,files,simple,user,views,admin,user_functions,user_management,db_users
from myapp import views_user
from django.views.generic import RedirectView
from django.templatetags.static import static

favicon_view = RedirectView.as_view(url=static('/img/favicon.svg'), permanent=True)

urlpatterns = [
    
    path('favicon.svg', favicon_view),
    #path('favicon.png', favicon_view),
    re_path(r'^actuator/gateway/routes/?$', simple.actuator_gateway_routes, name='actuator_gateway_routes'),
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

    path('user_management/', user_management.user_management, name='user_management'),
    path('user_management/create/', user_management.create_accounts_view, name='user_management_create'),
    path('user_management/prefix-check/', user_management.prefix_check, name='user_management_prefix_check'),
    path('user_management/bulk/', user_management.bulk_action, name='user_management_bulk'),
    path('user_management/review/exit/', user_management.exit_review, name='user_management_review_exit'),
    path('user_management/review/<int:user_id>/', user_management.start_review, name='user_management_review'),
    path('user_management/role/<int:user_id>/', user_management.set_role, name='user_management_role'),

    path('db_users/', db_users.db_users, name='db_users'),
    path('db_users/create/', db_users.create_view, name='db_users_create'),
    path('db_users/bulk/', db_users.bulk_action, name='db_users_bulk'),
    path('db_users/access/', db_users.save_access, name='db_users_access'),

    path('sql_ide/', views.sql_ide, name='sql_ide'),
    path('user_databases.sqlite', files.read_file),
    path('user_databases/<str:username>.sqlite', files.read_file),

    path('api/', api.api_endpoints, name='api_endpoints'),
    path('api/sql/<str:filename>.sql', api.api_sql, name='api_sql'),
    path('api/sql/list', api.api_sql_list, name='api_sql_list'),
    path('api/sql/rename', api.api_sql_rename, name='api_sql_rename'),
    path('api/sql/run', api.api_run_sql, name='api_run_sql'),
    path('api/upload_db/', api.api_upload_db, name='api_upload_db'),
    path('api/editor_diagram.json', api.api_editor_diagram_json, name='api_editor_diagram_json'),
    path('api/db_diagram.json', api.api_db_diagram_json, name='api_db_diagram_json'),
    path('api/sql/resolve_subqueries', api.api_resolve_subqueries, name='api_resolve_subqueries'),
]