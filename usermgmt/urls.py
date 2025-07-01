from django.urls import path
from .views import user_list, view_citizenship_document

urlpatterns = [
    path('users/', user_list, name='user_list'),
    path('view_document/<int:user_id>/', view_citizenship_document, name='view_citizenship_document'),
] 