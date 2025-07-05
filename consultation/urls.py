from django.urls import path
from .views import create_proposal, proposal_list, proposal_detail, active_consultations, member_consultation_detail, consultation_result, moderate_comments

app_name = 'consultation'

urlpatterns = [
    path('', create_proposal, name='create_proposal'),
    path('list/', proposal_list, name='proposal_list'),
    path('<int:pk>/', proposal_detail, name='proposal_detail'),
    path('active-consultations/', active_consultations, name='active_consultations'),
    path('active-consultations/<int:pk>/', member_consultation_detail, name='member_consultation_detail'),
    path('<int:pk>/result/', consultation_result, name='consultation_result'),
    path('<int:pk>/moderate-comments/', moderate_comments, name='moderate_comments'),
] 