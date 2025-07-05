from django.urls import path
from . import views

app_name = 'hapumgmt'

urlpatterns = [
    path('', views.hapu_list, name='hapu_list'),
    path('create/', views.hapu_create, name='hapu_create'),
    path('<int:pk>/', views.hapu_detail, name='hapu_detail'),
    path('<int:pk>/edit/', views.hapu_edit, name='hapu_edit'),
    path('<int:pk>/archive/', views.hapu_archive, name='hapu_archive'),
    path('<int:pk>/unarchive/', views.hapu_unarchive, name='hapu_unarchive'),
] 