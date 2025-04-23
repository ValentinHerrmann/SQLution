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
    

    path('sql/', views.sql_query_view, name='sql'),
    path('db_models/', views.db_models, name='db_models'),
    path('sql_form/', views.sql_form, name='sql_form'),
    #path('logout/', auth_views.LogoutView.as_view(next_page=settings.LOGOUT_REDIRECT_URL), name='logout'),
    #path('redirect/', views.redirect_user, name='redirect_user'),
]