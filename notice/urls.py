from django.urls import path
from . import views

urlpatterns = [
    path('', views.notice_list, name='notice_list'),
    path('create/', views.create_notice, name='create_notice'),
    path('manage/', views.manage_notices, name='manage_notices'),
    path('<int:pk>/edit/', views.edit_notice, name='edit_notice'),
    path('<int:pk>/delete/', views.delete_notice, name='delete_notice'),
    path('<int:pk>/expire/', views.expire_notice, name='expire_notice'),
    path('<int:pk>/engagement/', views.notice_engagement, name='notice_engagement'),
    path('<int:pk>/', views.notice_detail, name='notice_detail'),
] 