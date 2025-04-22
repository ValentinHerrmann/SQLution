from django.urls import include, path, re_path
from . import views
from django.views.generic import RedirectView

favicon_view = RedirectView.as_view(url='/static/favicon.ico', permanent=True)

urlpatterns = [
    re_path(r'^favicon\.ico$', favicon_view),
    path('', views.home, name='home'),
    path('sql/', views.sql_query_view, name='sql'),
    path('upload_json/', views.upload_json, name='upload_json'),
    path('apollon/', views.apollon, name='apollon'),
    path('db_models/', views.db_models, name='db_models'),
    path('user_functions', views.index, name='user_functions'),
    path('admin/', views.index, name='admin'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('logged_out/', views.logged_out, name='logged_out'),
    path('download_db/', views.download_db, name='download_db'),
    path('upload_db/', views.upload_db, name='upload_db'),
    path('logged_in/', views.logged_in, name='logged_in'),
    #path('redirect/', views.redirect_user, name='redirect_user'),
]