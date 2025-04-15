from django.urls import include, path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('todos/', views.todos, name='todos'),
    path('sql/', views.sql_query_view, name='sql'),
    path('upload_json/', views.upload_json, name='upload_json'),
    path('apollon/', views.apollon, name='apollon'),
    path('db_models/', views.db_models, name='db_models'),
    path('index/', views.index, name='index'),
    path('admin/', views.index, name='admin'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('logged_out/', views.logged_out, name='logged_out'),
]