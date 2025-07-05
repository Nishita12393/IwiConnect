from django.urls import path
from . import views

app_name = 'iwimgmt'

urlpatterns = [
    path('', views.iwi_list, name='iwi_list'),
    path('create/', views.iwi_create, name='iwi_create'),
    path('<int:iwi_id>/', views.iwi_detail, name='iwi_detail'),
    path('<int:iwi_id>/edit/', views.iwi_edit, name='iwi_edit'),
    path('<int:iwi_id>/archive/', views.iwi_archive, name='iwi_archive'),
    path('<int:iwi_id>/unarchive/', views.iwi_unarchive, name='iwi_unarchive'),
] 