from django.urls import path
from .views import user_list, view_citizenship_document, manage_iwi_leaders, manage_hapu_leaders

app_name = 'usermgmt'

urlpatterns = [
    path('users/', user_list, name='user_list'),
    path('view_document/<int:user_id>/', view_citizenship_document, name='view_citizenship_document'),
    path('manage-iwi-leaders/', manage_iwi_leaders, name='manage_iwi_leaders'),
    path('manage-hapu-leaders/', manage_hapu_leaders, name='manage_hapu_leaders'),
] 