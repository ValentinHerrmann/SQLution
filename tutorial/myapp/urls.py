from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('todos/', views.todos, name='todos'),
    path('sql/', views.sql_query_view, name='sql'),
    path('upload_json', views.upload_json, name='upload_json'),
]